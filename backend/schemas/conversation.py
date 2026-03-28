from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    owner_user_id: int
    title: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)
