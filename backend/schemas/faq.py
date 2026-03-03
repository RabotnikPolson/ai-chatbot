from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FAQCreate(BaseModel):
    title: str
    content: str

class FAQResponse(BaseModel):
    id: int
    title: str
    content: str
    updated_at: datetime

    # class Config:
    #     from_attributes = True
    model_config = ConfigDict(from_attributes = True)
