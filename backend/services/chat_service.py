from sqlalchemy.orm import Session
from fastapi import HTTPException
import json
import uuid
import redis

from db.models import Conversation, Message, MessageRoleEnum, MessageStatusEnum
from schemas.conversation import ConversationCreate
from schemas.message import MessageCreate
from workers.tasks import generate_reply
from services.logger import setup_json_logger

json_logger = setup_json_logger("chat_service_logger")

class ChatService:
    @staticmethod
    def create_conversation(db: Session, user_id: int, title: str) -> Conversation:
        new_conv = Conversation(owner_user_id=user_id, title=title)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        return new_conv

    @staticmethod
    def get_user_conversations(db: Session, user_id: int, page: int, limit: int):
        return db.query(Conversation).filter(
            Conversation.owner_user_id == user_id
        ).offset((page - 1) * limit).limit(limit).all()

    @staticmethod
    def get_conversation_by_id(db: Session, conv_id: int, user_id: int) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.owner_user_id == user_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Диалог не найден или у вас нет к нему доступа")
        return conv

    @staticmethod
    def delete_conversation(db: Session, conv_id: int, user_id: int):
        conv = ChatService.get_conversation_by_id(db, conv_id, user_id)
        db.delete(conv)
        db.commit()

    @staticmethod
    def send_message(db: Session, user_id: int, conversation_id: int, text: str, redis_client: redis.Redis) -> Message:
        chat = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.owner_user_id == user_id
        ).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        # 2. Сохраняем сообщение пользователя в БД
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRoleEnum.user,
            content=text,
            status=MessageStatusEnum.done
        )
        db.add(user_message)
        db.commit()

        # 3. Создаем "пустое" сообщение для ассистента со статусом queued
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRoleEnum.assistant,
            content="",
            status=MessageStatusEnum.queued
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        generate_reply.delay(assistant_message.id)

        # Update cache
        cache_key = f"conversation:{conversation_id}:last_messages"
        cached_history_raw = redis_client.get(cache_key)
        if cached_history_raw:
            try:
                cached_history = json.loads(cached_history_raw)
                cached_history.append({
                    "role": user_message.role.value,
                    "content": user_message.content
                })
                redis_client.setex(cache_key, 60, json.dumps(cached_history))
            except json.JSONDecodeError:
                redis_client.delete(cache_key)

        req_id = str(uuid.uuid4())
        json_logger.info("Сообщение поставлено в очередь", extra={
            "custom_fields": {
                "request_id": req_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message_id": assistant_message.id,
                "status": "queued",
                "latency_ms": 0
            }
        })

        return assistant_message

    @staticmethod
    def get_message(db: Session, message_id: int, user_id: int) -> Message:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")

        chat = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
        if not chat or chat.owner_user_id != user_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        return message

    @staticmethod
    def get_conversation_messages(db: Session, conversation_id: int, user_id: int):
        chat = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.owner_user_id == user_id
        ).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        return messages

chat_service = ChatService()
