from unittest.mock import patch
from db.models import Message, MessageStatusEnum
from uuid import UUID

def test_send_message(client):
    # 1. Arrange: Создаем юзера, получаем токен, создаем чат
    client.post("/auth/register", json={"email": "msg_user@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "msg_user@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post("/conversations/", json={"title": "Чат для сообщений"}, headers=headers)
    conv_id = conv_resp.json()["id"]

    # 2. Act: Отправляем сообщение.
    # ГЛУШИМ СРАЗУ И ВОРКЕР, И REDIS
    with patch("services.chat_service.generate_reply.delay") as mock_task, \
            patch("api.conversations.redis_client.get", return_value=None), \
            patch("api.conversations.redis_client.setex"), \
            patch("api.conversations.redis_client.delete"):
        response = client.post(
            f"/conversations/{conv_id}/messages",
            json={"text": "Привет, бот!"},
            headers=headers
        )

    # 3. Assert: Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "message_id" in data
    assert data["status"] == "queued"

    UUID(data["message_id"])
    mock_task.assert_called_once()
    queued_message_id, queued_temperature = mock_task.call_args.args
    assert isinstance(queued_message_id, int)
    assert queued_temperature == 0.7


def test_send_message_with_temperature(client):
    client.post("/auth/register", json={"email": "msg_user_temp@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "msg_user_temp@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post("/conversations/", json={"title": "Чат для температуры"}, headers=headers)
    conv_id = conv_resp.json()["id"]

    with patch("services.chat_service.generate_reply.delay") as mock_task, \
            patch("api.conversations.redis_client.get", return_value=None), \
            patch("api.conversations.redis_client.setex"), \
            patch("api.conversations.redis_client.delete"):
        response = client.post(
            f"/conversations/{conv_id}/messages",
            json={"text": "Сгенерируй ответ", "temperature": 0.2},
            headers=headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    UUID(data["message_id"])
    mock_task.assert_called_once()
    queued_message_id, queued_temperature = mock_task.call_args.args
    assert isinstance(queued_message_id, int)
    assert queued_temperature == 0.2


def test_get_message_status(client):
    # 1. Arrange: Настраиваем окружение
    client.post("/auth/register", json={"email": "msg_user2@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "msg_user2@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post("/conversations/", json={"title": "Чат 2"}, headers=headers)
    conv_id = conv_resp.json()["id"]

    # Отправляем сообщение (снова глушим и Celery, и Redis)
    with patch("services.chat_service.generate_reply.delay"), \
            patch("api.conversations.redis_client.get", return_value=None), \
            patch("api.conversations.redis_client.setex"), \
            patch("api.conversations.redis_client.delete"):
        msg_resp = client.post(
            f"/conversations/{conv_id}/messages",
            json={"text": "Как дела?"},
            headers=headers
        )
    msg_id = msg_resp.json()["message_id"]

    # 2. Act: Дергаем эндпоинт получения статуса
    response = client.get(f"/messages/{msg_id}", headers=headers)

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == msg_id
    assert data["status"] == "queued"


def test_retry_creates_new_assistant_message(client, db_session):
    client.post("/auth/register", json={"email": "msg_retry@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "msg_retry@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post("/conversations/", json={"title": "Чат retry"}, headers=headers)
    conv_id = conv_resp.json()["id"]

    with patch("services.chat_service.generate_reply.delay") as mock_task, \
            patch("api.conversations.redis_client.get", return_value=None), \
            patch("api.conversations.redis_client.setex"), \
            patch("api.conversations.redis_client.delete"):
        msg_resp = client.post(
            f"/conversations/{conv_id}/messages",
            json={"text": "Сломайся"},
            headers=headers
        )
        original_id = msg_resp.json()["message_id"]

        # Simulate worker failure so retry path starts from failed message.
        original_msg = db_session.query(Message).filter(Message.public_id == original_id).first()
        original_msg.status = MessageStatusEnum.failed
        original_msg.error = "boom"
        db_session.commit()

        retry_resp = client.post(f"/messages/{original_id}/retry", headers=headers)

    assert retry_resp.status_code == 200
    retried_data = retry_resp.json()
    assert retried_data["id"] != original_id
    assert retried_data["status"] == "queued"

    old_msg_resp = client.get(f"/messages/{original_id}", headers=headers)
    assert old_msg_resp.status_code == 200
    assert old_msg_resp.json()["status"] == "failed"

    assert mock_task.call_count == 2
    first_call_id, first_call_temp = mock_task.call_args_list[0].args
    second_call_id, second_call_temp = mock_task.call_args_list[1].args
    assert isinstance(first_call_id, int)
    assert isinstance(second_call_id, int)
    assert first_call_id != second_call_id
    assert first_call_temp == 0.7
    assert second_call_temp == 0.7


def test_retry_rejects_non_failed_assistant_message(client):
    client.post("/auth/register", json={"email": "msg_retry_non_failed@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "msg_retry_non_failed@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    conv_resp = client.post("/conversations/", json={"title": "Чат retry guard"}, headers=headers)
    conv_id = conv_resp.json()["id"]

    with patch("services.chat_service.generate_reply.delay"), \
            patch("api.conversations.redis_client.get", return_value=None), \
            patch("api.conversations.redis_client.setex"), \
            patch("api.conversations.redis_client.delete"):
        msg_resp = client.post(
            f"/conversations/{conv_id}/messages",
            json={"text": "Ответь"},
            headers=headers,
        )

    queued_assistant_id = msg_resp.json()["message_id"]
    retry_resp = client.post(f"/messages/{queued_assistant_id}/retry", headers=headers)

    assert retry_resp.status_code == 400
    assert "failed" in retry_resp.json()["detail"]

