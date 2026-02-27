import os
import redis
import json

import logging
logger = logging.getLogger(__name__)

from workers.celery_app import celery_app
from db.database import SessionLocal
from db.models import Message, MessageStatusEnum
from providers.ollama import OllamaProvider

# Подключаемся к Redis напрямую
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)

@celery_app.task(name="generate_reply")
def generate_reply(message_id: int):
    db = SessionLocal()
    try:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            return "Message not found"

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

        # === 2. БЛОК ГЕНЕРАЦИИ И СТРИМИНГА ===
        # Вызываем провайдер только один раз!
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

        # === 3. СОХРАНЕНИЕ РЕЗУЛЬТАТА ===
        msg.content = full_answer
        msg.status = MessageStatusEnum.done
        msg.provider = "ollama"
        db.commit()

        return "Success"

    except Exception as e:
        db.rollback()
        if msg:
            msg.status = MessageStatusEnum.failed
            msg.error = str(e)
            db.commit()
            redis_client.publish(f"chat_stream_{message_id}", "[ERROR]")
        raise e
    finally:
        db.close()