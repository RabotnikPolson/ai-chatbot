from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from db.models import MessageRoleEnum, MessageStatusEnum

class MessageCreate(BaseModel):
    text: str
    temperature: Optional[float] = None


class SendMessageResponse(BaseModel):
    message_id: UUID
    status: MessageStatusEnum


class MessageResponse(BaseModel):
    id: UUID = Field(validation_alias="public_id")
    conversation_id: int
    role: MessageRoleEnum
    content: str
    status: MessageStatusEnum


    provider: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)
