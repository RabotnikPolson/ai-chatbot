from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class FAQCreate(BaseModel):
    title: str
    content: str
    tags: str

class FAQResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: str
    updated_at: datetime

    # class Config:
    #     from_attributes = True
    model_config = ConfigDict(from_attributes = True)
