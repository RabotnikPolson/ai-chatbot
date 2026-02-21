from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from schemas.user import UserCreate, UserResponse
from db.models import User
from services.security import get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Проверяем, свободен ли email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже занят")

    # 2. Прячем пароль и создаем пользователя
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_pwd)

    # 3. Сохраняем в базу
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user