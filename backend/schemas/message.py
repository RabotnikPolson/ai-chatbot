from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from db.models import MessageRoleEnum, MessageStatusEnum

# 1. Что мы ждем от фронтенда при отправке сообщения
class MessageCreate(BaseModel):
    text: str
    temperature: Optional[float] = None


class SendMessageResponse(BaseModel):
    message_id: UUID
    status: MessageStatusEnum

# 2. Что мы возвращаем на фронтенд
class MessageResponse(BaseModel):
    id: UUID = Field(validation_alias="public_id")
    conversation_id: int
    role: MessageRoleEnum
    content: str
    status: MessageStatusEnum

    # Эти поля могут быть пустыми (None), пока бот не ответит
    provider: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)
