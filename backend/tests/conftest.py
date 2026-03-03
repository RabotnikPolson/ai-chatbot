import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Импортируем наше приложение и зависимости
from main import app
from db.database import Base
from api.auth import get_db

# 1. Настраиваем тестовую базу данных (SQLite в оперативной памяти)
# SQLite работает мгновенно и не требует поднятия реального Postgres для тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Специфика SQLite
    poolclass=StaticPool, # База живет в памяти, пока работает тест
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Фикстура для базы данных
# Фикстура — это функция, которая подготавливает данные для теста
@pytest.fixture()
def db_session():
    # Создаем все таблицы в тестовой базе
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db # Отдаем сессию тесту
    finally:
        db.close()
        # После окончания теста удаляем все таблицы, чтобы следующий тест был чистым
        Base.metadata.drop_all(bind=engine)

# 3. Фикстура для тестового клиента
@pytest.fixture()
def client(db_session):
    # Функция для подмены оригинальной базы на тестовую
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Говорим FastAPI: "Когда кто-то просит get_db, дай ему override_get_db"
    app.dependency_overrides[get_db] = override_get_db

    # Создаем клиента и отдаем его тесту
    with TestClient(app) as c:
        yield c