import os
import redis
from fastapi.responses import StreamingResponse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import jwt
import json

from schemas.conversation import ConversationCreate, ConversationResponse
from api.auth import oauth2_scheme, get_db
from services.security import SECRET_KEY, ALGORITHM

from db.models import Message, MessageStatusEnum
from schemas.message import MessageCreate, MessageResponse
from services.chat_service import ChatService


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)

router = APIRouter(prefix="/conversations", tags=["conversations"])
messages_router = APIRouter(prefix="/messages", tags=["messages"])

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload.get("sub"))


@router.post("/", response_model=ConversationResponse)
def create_conversation(
        conv_data: ConversationCreate,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    return ChatService.create_conversation(db, user_id, conv_data.title)

@router.get("/", response_model=List[ConversationResponse])
def get_conversations(
        page: int = 1,
        limit: int = 20,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    return ChatService.get_user_conversations(db, user_id, page, limit)


@router.get("/{id}", response_model=ConversationResponse)
def get_conversation(
        id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    return ChatService.get_conversation_by_id(db, id, user_id)


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
        conversation_id: int,
        message_data: MessageCreate,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    return ChatService.send_message(db, user_id, conversation_id, message_data.text, redis_client)


@messages_router.get("/{message_id}", response_model=MessageResponse)
def get_message_status(
        message_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    return ChatService.get_message(db, message_id, user_id)

# SSE
@messages_router.get("/{message_id}/stream")
def stream_message(
        message_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    message = ChatService.get_message(db, message_id, user_id)

    if message.status == MessageStatusEnum.done:
        return StreamingResponse(iter([f"data: [DONE]\n\n"]), media_type="text/event-stream")

    def event_generator():
        pubsub = redis_client.pubsub()
        channel_name = f"chat_stream_{message_id}"
        pubsub.subscribe(channel_name)

        try:
            for redis_msg in pubsub.listen():
                if redis_msg["type"] == "message":
                    data = redis_msg["data"].decode("utf-8")
                    if data == "[DONE]":
                        yield f"data: [DONE]\n\n"
                        break
                    elif data == "[ERROR]":
                        yield f"data: [ERROR]\n\n"
                        break
                    else:
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        finally:
            pubsub.unsubscribe(channel_name)
            pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_chat_history(
        conversation_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    return ChatService.get_conversation_messages(db, conversation_id, user_id)


@router.delete("/{id}")
def delete_conversation(
        id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    ChatService.delete_conversation(db, id, user_id)
    return {"message": "Диалог удален"}