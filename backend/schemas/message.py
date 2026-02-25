from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from db.models import MessageRoleEnum, MessageStatusEnum

# 1. Что мы ждем от фронтенда при отправке сообщения
class MessageCreate(BaseModel):
    text: str

# 2. Что мы возвращаем на фронтенд
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRoleEnum
    content: str
    status: MessageStatusEnum

    # Эти поля могут быть пустыми (None), пока бот не ответит
    provider: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True # Позволяет Pydantic читать данные напрямую из модели базы данных