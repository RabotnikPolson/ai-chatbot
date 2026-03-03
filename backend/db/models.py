from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"

class MessageRoleEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"

class MessageStatusEnum(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.user)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship("Conversation", back_populates="owner")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True) # Название чата (может быть пустым)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="conversations")
    # Это позволит нам обращаться к списку сообщений чата вот так: my_chat.messages
    # если мы удалим чат, база автоматически удалит все связанные с ним сообщения
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    # Вот тот самый внешний ключ, про который ты говорил:
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)

    role = Column(Enum(MessageRoleEnum), nullable=False)
    content = Column(String, nullable=False) # Текст сообщения
    status = Column(Enum(MessageStatusEnum), default=MessageStatusEnum.queued)

    # Поля для аналитики и дебага нейросети (пока могут быть пустыми)
    provider = Column(String, default="ollama")
    latency_ms = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь для Питона, чтобы мы могли писать message.conversation
    conversation = relationship("Conversation", back_populates="messages")

class FAQItem(Base):
    __tablename__ = "faq_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    tags = Column(String, nullable=True) # Добавлено по ТЗ
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())