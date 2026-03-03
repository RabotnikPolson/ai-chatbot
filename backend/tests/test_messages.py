from unittest.mock import patch

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
    assert data["role"] == "assistant"
    assert data["status"] == "queued"
    assert "id" in data

    mock_task.assert_called_once_with(data["id"])


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
    msg_id = msg_resp.json()["id"]

    # 2. Act: Дергаем эндпоинт получения статуса
    response = client.get(f"/messages/{msg_id}", headers=headers)

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == msg_id
    assert data["status"] == "queued"