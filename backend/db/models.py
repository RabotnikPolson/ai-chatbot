from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey # <-- Добавили ForeignKey
from sqlalchemy.orm import relationship # <-- Добавили relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.user)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # НОВОЕ: Связь для Питона (чтобы можно было сказать: user.conversations и получить список его чатов)
    conversations = relationship("Conversation", back_populates="owner")

# НОВЫЙ КЛАСС:
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    # ForeignKey жестко говорит базе: "Смотри в таблицу users, в колонку id"
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True) # Название чата (может быть пустым)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь для Питона (чтобы можно было сказать: conversation.owner и получить данные юзера)
    owner = relationship("User", back_populates="conversations")