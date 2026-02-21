from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import jwt

from db.database import SessionLocal
from db.models import Conversation
from schemas.conversation import ConversationCreate, ConversationResponse
from api.auth import oauth2_scheme, get_db
from services.security import SECRET_KEY, ALGORITHM

# Создаем роутер для диалогов
router = APIRouter(prefix="/conversations", tags=["conversations"])

# Вспомогательная функция: достает ID пользователя из его токена
def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload.get("sub"))

# Эндпоинт 1: Создать новый чат
@router.post("/", response_model=ConversationResponse)
def create_conversation(
        conv_data: ConversationCreate,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Требуем токен!
):
    # Создаем чат, привязывая его к ID пользователя из токена
    new_conv = Conversation(owner_user_id=user_id, title=conv_data.title)
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv

# Эндпоинт 2: Получить список всех чатов текущего пользователя
@router.get("/", response_model=List[ConversationResponse])
def get_conversations(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id) # Требуем токен!
):
    # Ищем в базе только те чаты, у которых owner_user_id совпадает с нашим
    return db.query(Conversation).filter(Conversation.owner_user_id == user_id).all()