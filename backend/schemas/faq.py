from pydantic import BaseModel
from datetime import datetime

class FAQCreate(BaseModel):
    title: str
    content: str

class FAQResponse(BaseModel):
    id: int
    title: str
    content: str
    updated_at: datetime

    class Config:
        from_attributes = True