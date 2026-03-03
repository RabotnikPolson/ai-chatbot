import os
import redis
import json
import logging
import time


from sqlalchemy import or_  # Импортируем or_ для поиска ИЛИ

from workers.celery_app import celery_app
from db.database import SessionLocal
from db.models import Message, MessageStatusEnum, FAQItem  # Добавили FAQItem
from providers.ollama import OllamaProvider

from services.logger import setup_json_logger

# Создаем логгер для воркера
json_logger = setup_json_logger("worker_logger")

logger = logging.getLogger(__name__)

# Подключаемся к Redis напрямую
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)

@celery_app.task(bind=True, name="generate_reply", max_retries=3, default_retry_delay=5)
def generate_reply(self, message_id: int):
    with SessionLocal() as db:
        try:
            # Получаем ПУСТОЕ сообщение ассистента, которое мы создали в API
            msg = db.query(Message).filter(Message.id == message_id).first()
            if not msg:
                return "Message not found"
    
            if msg.status == MessageStatusEnum.done:
                return "Already done"
    
            msg.status = MessageStatusEnum.processing
            db.commit()
    
            # === 1. БЛОК КЭШИРОВАНИЯ ИСТОРИИ ===
            cache_key = f"conversation:{msg.conversation_id}:last_messages"
            cached_history = redis_client.get(cache_key)

            if cached_history:
                # CACHE HIT
                logger.info(f"CACHE HIT: Достали историю из Redis для чата {msg.conversation_id}")
                messages_for_ollama = json.loads(cached_history)
            else:
                # CACHE MISS
                logger.info(f"CACHE MISS: Идем в базу данных для чата {msg.conversation_id}")
    
                history = db.query(Message).filter(
                    Message.conversation_id == msg.conversation_id,
                    Message.id != message_id,
                    Message.status == MessageStatusEnum.done
                ).order_by(Message.created_at.desc()).limit(20).all()
    
                history = history[::-1]
    
                messages_for_ollama = []
                for h_msg in history:
                    messages_for_ollama.append({
                        "role": h_msg.role.value,
                        "content": h_msg.content
                    })
    
                redis_client.setex(cache_key, 60, json.dumps(messages_for_ollama))
    
            # === RAG-lite: БЛОК ЗНАНИЙ ИЗ FAQ ===
            # Берем текст пользователя (он будет последним в списке сообщений)
            user_query = ""
            if messages_for_ollama and messages_for_ollama[-1]["role"] == "user":
                user_query = messages_for_ollama[-1]["content"]
    
            if user_query:
                # Ищем совпадения в базе FAQ
                search_text = f"%{user_query}%"
                relevant_faqs = db.query(FAQItem).filter(
                    or_(
                        FAQItem.title.ilike(search_text),
                        FAQItem.content.ilike(search_text)
                    )
                ).limit(3).all()
    
                if relevant_faqs:
                    # Если что-то нашли, собираем в текст
                    faq_context = "\n\n".join([f"Вопрос: {faq.title}\nОтвет: {faq.content}" for faq in relevant_faqs])
    
                    system_prompt = (
                        "Ты — корпоративный ИИ-помощник. "
                        "Используй следующую информацию из базы знаний компании (FAQ) для ответа на вопрос пользователя:\n\n"
                        f"{faq_context}\n\n"
                        "Отвечай вежливо и опирайся на предоставленные знания."
                    )
    
                    # Вставляем системный промпт в самое начало контекста
                    messages_for_ollama.insert(0, {
                        "role": "system",
                        "content": system_prompt
                    })
    
            start_time = time.time()
            # === 2. БЛОК ГЕНЕРАЦИИ И СТРИМИНГА ===
            provider = OllamaProvider(model="qwen2.5:0.5b")
    
            full_answer = ""
            channel_name = f"chat_stream_{message_id}"
    
            # Итерируемся по генератору (получаем кусочки текста)
            for chunk in provider.generate_stream(messages=messages_for_ollama):
                full_answer += chunk # Приклеиваем кусочек к полному ответу
                # Вещаем этот кусочек в радиоканал Redis!
                redis_client.publish(channel_name, chunk)
    
            # Сигнал окончания стрима
            redis_client.publish(channel_name, "[DONE]")
    
            # Обновляем кэш с ответом бота
            if cached_history:
                try:
                    # В случае CACHE HIT мы уже распарсили messages_for_ollama
                    # Но мы могли добавить системный промпт в начало, поэтому берем оригинальный кэш
                    current_cache = json.loads(redis_client.get(cache_key) or "[]")
                    current_cache.append({
                        "role": "assistant",
                        "content": full_answer
                    })
                    redis_client.setex(cache_key, 60, json.dumps(current_cache))
                except json.JSONDecodeError:
                    pass
    
    
            # === 3. СОХРАНЕНИЕ РЕЗУЛЬТАТА ===
            msg.content = full_answer
            msg.status = MessageStatusEnum.done
            msg.provider = "ollama"
            db.commit()
    
            # Считаем разницу во времени и переводим в миллисекунды
            latency_ms = int((time.time() - start_time) * 1000)
    
            json_logger.info("Генерация ответа успешно завершена", extra={
                "custom_fields": {
                    "request_id": "worker",
                    "user_id": msg.conversation.owner_user_id if msg.conversation else None,
                    "conversation_id": msg.conversation_id,
                    "message_id": msg.id,
                    "status": "done",
                    "latency_ms": latency_ms
                }
            })
    
            return "Success"
    
        except Exception as e:
            # Save these before rollback causes DetachedInstanceError
            conversation_id = msg.conversation_id if msg else None
            owner_user_id = msg.conversation.owner_user_id if msg and msg.conversation else None
            message_obj_id = msg.id if msg else None
            
            db.rollback()
            
            # Retry mechanism
            if self.request.retries < self.max_retries:
                json_logger.warning(f"Ошибка при генерации, попытка повтора ({self.request.retries + 1}/{self.max_retries}): {str(e)}")
                raise self.retry(exc=e)
            
            # If all retries failed or MaxRetriesExceededError
            if msg:
                # We need to re-fetch or just update the status without lazy-loading relations
                fail_msg = db.query(Message).filter(Message.id == message_obj_id).first()
                if fail_msg:
                    fail_msg.status = MessageStatusEnum.failed
                    fail_msg.error = str(e)
                    db.commit()
                redis_client.publish(f"chat_stream_{message_id}", "[ERROR]")

            latency_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
            json_logger.error(f"Ошибка при генерации ответа: {str(e)}", extra={
                "custom_fields": {
                    "request_id": "worker",
                    "user_id": owner_user_id,
                    "conversation_id": conversation_id,
                    "message_id": message_obj_id,
                    "status": "failed",
                    "latency_ms": latency_ms
                }
            })
            raise e