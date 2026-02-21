from pydantic import BaseModel, EmailStr
from datetime import datetime
from db.models import RoleEnum

# Это то, что мы ЖДЕМ от пользователя при регистрации
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Это то, что мы ОТДАЕМ обратно (обрати внимание, пароля тут нет!)
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