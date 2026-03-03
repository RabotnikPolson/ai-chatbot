# tests/test_worker.py
from unittest.mock import patch, MagicMock
from providers.ollama import OllamaProvider
from workers.tasks import generate_reply
from db.models import User, Conversation, Message, MessageStatusEnum

def test_ollama_provider_mock():
    # 1. Arrange: Создаем провайдер
    provider = OllamaProvider()

    # Мокаем библиотеку requests.post, чтобы она не делала реальный запрос в интернет
    with patch("providers.ollama.requests.post") as mock_post:
        # Настраиваем "фейковый" ответ, который вернет мок
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Я фейковая нейросеть"}}
        mock_post.return_value = mock_response

        # 2. Act: Вызываем метод генерации
        answer = provider.generate(messages=[{"role": "user", "content": "Привет"}])

        # 3. Assert: Проверяем, что провайдер вернул нужный текст и запрос был сделан 1 раз
        assert answer == "Я фейковая нейросеть"
        mock_post.assert_called_once()


def test_worker_idempotency(db_session):
    # 1. Arrange: Создаем данные напрямую в тестовой базе данных
    user = User(email="worker@test.com", password_hash="123")
    db_session.add(user)
    db_session.commit()

    conv = Conversation(owner_user_id=user.id, title="Test")
    db_session.add(conv)
    db_session.commit()

    # ВАЖНО: Создаем сообщение, которое УЖЕ выполнено (status = done)
    msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content="Уже готово",
        status=MessageStatusEnum.done
    )
    db_session.add(msg)
    db_session.commit()

    # 2. Act: Вызываем воркер.
    # Глушим Redis и подменяем SessionLocal, чтобы воркер полез в нашу тестовую базу (db_session), а не в основную!
    with patch("workers.tasks.SessionLocal", return_value=db_session), \
            patch("workers.tasks.redis_client"):

        result = generate_reply(msg.id)

    # 3. Assert: Воркер должен отказаться работать и вернуть нашу фразу "Already done"
    assert result == "Already done"