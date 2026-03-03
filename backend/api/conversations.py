import uuid
from services.logger import setup_json_logger

import os
import redis
from fastapi.responses import StreamingResponse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import jwt
from workers.tasks import generate_reply

from db.database import SessionLocal
from db.models import Conversation
from schemas.conversation import ConversationCreate, ConversationResponse
from api.auth import oauth2_scheme, get_db
from services.security import SECRET_KEY, ALGORITHM

from db.models import Message, MessageRoleEnum, MessageStatusEnum
from schemas.message import MessageCreate, MessageResponse


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)
# Создаем роутер для диалогов
router = APIRouter(prefix="/conversations", tags=["conversations"])

json_logger = setup_json_logger("api_logger")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload.get("sub"))


@router.post("/", response_model=ConversationResponse)
def create_conversation(
        conv_data: ConversationCreate,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Требуем токен!
):
    # Создаем чат, привязывая его к ID пользователя из токена
    new_conv = Conversation(owner_user_id=user_id, title=conv_data.title)
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv

# Эндпоинт 2: Получить список всех чатов текущего пользователя
@router.get("/", response_model=List[ConversationResponse])
def get_conversations(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Требуем токен!
):
    # Ищем в базе только те чаты, у которых owner_user_id совпадает с нашим
    return db.query(Conversation).filter(Conversation.owner_user_id == user_id).all()


# Эндпоинт 3: Получить детали конкретного чата
@router.get("/{id}", response_model=ConversationResponse)
def get_conversation(
        id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    # Ищем чат по ID, при этом проверяем, что он принадлежит текущему пользователю
    conv = db.query(Conversation).filter(Conversation.id == id, Conversation.owner_user_id == user_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Диалог не найден или у вас нет к нему доступа")
    return conv


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
        conversation_id: int, # FastAPI автоматически возьмет это из URL /{conversation_id}/messages
        message_data: MessageCreate, # Pydantic проверит JSON тело (наш текст)
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Проверяем, что юзер авторизован
):
    # 1. Проверяем, существует ли такой чат вообще и принадлежит ли он этому юзеру
    chat = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_user_id == user_id
    ).first()

    # Если чата нет или он чужой — кидаем ошибку 404
    if not chat:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Чат не найден")

    # 2. Сохраняем сообщение пользователя в БД
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRoleEnum.user,
        content=message_data.text, # Берем text из схемы и кладем в content модели БД
        status=MessageStatusEnum.done # Сообщение юзера всегда "done", он же его уже написал
    )
    db.add(user_message)
    db.commit()

    # 3. Создаем "пустое" сообщение для ассистента со статусом queued (как просит ТЗ)
    assistant_message = Message(
        conversation_id=conversation_id,
        role=MessageRoleEnum.assistant,
        content="", # Пока пустое, бот еще думает
        status=MessageStatusEnum.queued
    )


    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    generate_reply.delay(assistant_message.id)
    # ТЗ просит возвращать статус "queued" и message_id
    # Наш MessageResponse как раз вернет данные assistant_message

    cache_key = f"conversation:{conversation_id}:last_messages"
    redis_client.delete(cache_key)

    #uid for http request
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

from fastapi import HTTPException

# Эндпоинт 4: Получить статус и текст конкретного сообщения
@router.get("/messages/{message_id}", response_model=MessageResponse)
def get_message_status(
        message_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Защита: проверяем, что юзер залогинен
):
    # Ищем сообщение в базе
    message = db.query(Message).filter(Message.id == message_id).first()

    # Если сообщения нет, отдаем ошибку 404
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")

    # Дополнительная проверка безопасности:
    # Убеждаемся, что чат, к которому привязано сообщение, принадлежит этому юзеру
    chat = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    if not chat or chat.owner_user_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    return message

# SSE
@router.get("/messages/{message_id}/stream")
def stream_message(
        message_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Защита от чужих глаз
):
    # 1. Проверяем, существует ли сообщение и принадлежит ли оно юзеру
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")

    chat = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    if not chat or chat.owner_user_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Если сообщение уже готово (мы опоздали), нет смысла слушать радио, стрим окончен
    if message.status == MessageStatusEnum.done:
        return StreamingResponse(iter([f"data: [DONE]\n\n"]), media_type="text/event-stream")

    # 2. Функция-генератор, которая слушает Redis и отдает данные в браузер
    def event_generator():
        # Подключаемся к механизму Pub/Sub
        pubsub = redis_client.pubsub()
        channel_name = f"chat_stream_{message_id}"

        # Настраиваемся на нужную "радиоволну"
        pubsub.subscribe(channel_name)

        try:
            # Бесконечно слушаем новые сообщения в канале
            for redis_msg in pubsub.listen():
                # pubsub.listen() при старте отдает системное сообщение об успешной подписке.
                # Нам нужны только реальные сообщения (type == 'message')
                if redis_msg["type"] == "message":
                    # Данные из Redis приходят в виде байтов (b'text'), декодируем их в строку
                    data = redis_msg["data"].decode("utf-8")

                    if data == "[DONE]":
                        # Если воркер закончил работу, отправляем финальный маркер и разрываем соединение
                        yield f"data: [DONE]\n\n"
                        break
                    elif data == "[ERROR]":
                        yield f"data: [ERROR]\n\n"
                        break
                    else:
                        # Форматируем по стандарту SSE: "data: {наш_кусочек}\n\n"
                        yield f"data: {data}\n\n"
        finally:
            # Обязательно отписываемся от канала, когда пользователь закрыл вкладку или ответ получен
            pubsub.unsubscribe(channel_name)
            pubsub.close()

    # 3. Возвращаем специальный ответ, который держит соединение открытым
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# history for front
@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_chat_history(
        conversation_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    chat = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_user_id == user_id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    # старые сверху
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return messages


@router.delete("/{id}")
def delete_conversation(
        id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    conv = db.query(Conversation).filter(Conversation.id == id, Conversation.owner_user_id == user_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Диалог не найден или у вас нет к нему доступа")

    db.delete(conv)
    db.commit()
    return {"message": "Диалог удален"}