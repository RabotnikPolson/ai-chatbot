from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# Что мы ждем при создании чата (название может быть пустым)
class ConversationCreate(BaseModel):
    title: Optional[str] = None

# Что мы отдаем обратно
class ConversationResponse(BaseModel):
    id: int
    owner_user_id: int
    title: Optional[str]
    created_at: datetime

    # class Config:
    #     from_attributes = True
    model_config = ConfigDict(from_attributes = True)
