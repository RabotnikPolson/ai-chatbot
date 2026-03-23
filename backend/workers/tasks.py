import os
import redis
import json
import logging
import time


from sqlalchemy import or_

from workers.celery_app import celery_app
from db.database import SessionLocal
from db.models import Message, MessageStatusEnum, FAQItem, MessageRoleEnum
from providers.ollama import OllamaProvider

from services.logger import setup_json_logger

json_logger = setup_json_logger("worker_logger")

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)

@celery_app.task(bind=True, name="generate_reply", max_retries=3, default_retry_delay=5)
def generate_reply(self, message_id: int, temperature: float = 0.7):
    with SessionLocal() as db:
        try:
            msg = db.query(Message).filter(Message.id == message_id).first()
            if not msg:
                return "Message not found"
    
            if msg.status == MessageStatusEnum.done:
                return "Already done"
    
            msg.status = MessageStatusEnum.processing
            db.commit()
    
            cache_key = f"conversation:{msg.conversation_id}:last_messages"
            cached_history = redis_client.get(cache_key)

            if cached_history:
                logger.info(f"CACHE HIT: Достали историю из Redis для чата {msg.conversation_id}")
                messages_for_ollama = json.loads(cached_history)
            else:
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
    
            user_query = ""
            if messages_for_ollama and messages_for_ollama[-1]["role"] == "user":
                user_query = messages_for_ollama[-1]["content"]
            else:
                last_user_msg = db.query(Message).filter(
                    Message.conversation_id == msg.conversation_id,
                    Message.role == MessageRoleEnum.user
                ).order_by(Message.created_at.desc()).first()
                if last_user_msg:
                    user_query = last_user_msg.content

            system_faqs = db.query(FAQItem).filter(
                or_(
                    FAQItem.tags.ilike('%system%'),
                    FAQItem.tags.ilike('%global%'),
                    FAQItem.title.ilike('%тон%'),
                    FAQItem.title.ilike('%роль%'),
                    FAQItem.title.ilike('%правил%')
                )
            ).all()

            relevant_faqs = []
            if user_query:
                import re
                words = [w for w in re.findall(r'\w+', user_query.lower()) if len(w) >= 3]
                if not words:
                    words = [user_query.lower()]
                
                conditions = []
                for word in words:
                    search_text = f"%{word}%"
                    conditions.append(FAQItem.title.ilike(search_text))
                    conditions.append(FAQItem.content.ilike(search_text))

                relevant_faqs = db.query(FAQItem).filter(
                    or_(*conditions)
                ).limit(3).all()

            combined_faqs = list({faq.id: faq for faq in system_faqs + relevant_faqs}.values())
            

    
            if combined_faqs:
                    faq_context = "\n\n".join([f"Правило: {faq.title}\nОписание: {faq.content}" for faq in combined_faqs])
    
                    system_prompt = (
                        "Ты — корпоративный ИИ-помощник. "
                        "Используй следующую информацию из базы знаний компании (FAQ) для ответа на вопросы пользователя. "
                        "Если там указана роль или тон общения - следуй им неукоснительно!\n\n"
                        f"{faq_context}\n\n"
                        "Отвечай вежливо и опирайся на предоставленные знания."
                    )
                    

    
                    messages_for_ollama.insert(0, {
                        "role": "system",
                        "content": system_prompt
                    })
    
            start_time = time.time()
            provider = OllamaProvider(model="qwen2.5:0.5b")
    
            full_answer = ""
            channel_name = f"chat_stream_{message_id}"
    
            for chunk in provider.generate_stream(messages=messages_for_ollama, temperature=temperature):
                full_answer += chunk

                redis_client.setex(f"chat_partial_{message_id}", 3600, full_answer)

                redis_client.publish(channel_name, full_answer)
    
            redis_client.publish(channel_name, "[DONE]")
    
            if cached_history:
                try:
                    current_cache = json.loads(redis_client.get(cache_key) or "[]")
                    current_cache.append({
                        "role": "assistant",
                        "content": full_answer
                    })
                    redis_client.setex(cache_key, 60, json.dumps(current_cache))
                except json.JSONDecodeError:
                    pass
    
    
            msg.content = full_answer
            msg.status = MessageStatusEnum.done
            msg.provider = "ollama"
            db.commit()
    
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
            conversation_id = msg.conversation_id if msg else None
            owner_user_id = msg.conversation.owner_user_id if msg and msg.conversation else None
            message_obj_id = msg.id if msg else None
            
            db.rollback()
            
            if self.request.retries < self.max_retries:
                json_logger.warning(f"Ошибка при генерации, попытка повтора ({self.request.retries + 1}/{self.max_retries}): {str(e)}")
                raise self.retry(exc=e)

            if msg:
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