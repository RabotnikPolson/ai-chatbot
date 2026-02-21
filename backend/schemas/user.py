from pydantic import BaseModel, EmailStr
from datetime import datetime
from db.models import RoleEnum

# what we except
class UserCreate(BaseModel):
    email: EmailStr
    password: str

#what we return
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"