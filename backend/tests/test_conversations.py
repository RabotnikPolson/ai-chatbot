# tests/test_conversations.py
from db.models import User, RoleEnum

def test_create_conversation(client):
    # 1. Arrange (Подготовка): Создаем юзера и получаем токен
    client.post("/auth/register", json={"email": "chat_user@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "chat_user@example.com", "password": "123"})
    token = login_resp.json()["access_token"]

    # Формируем заголовки запроса так, как это делает браузер
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Act (Действие): Создаем чат
    response = client.post("/conversations/", json={"title": "Мой первый тестовый чат"}, headers=headers)

    # 3. Assert (Проверка)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Мой первый тестовый чат"
    assert "id" in data

def test_get_conversations(client):
    # 1. Arrange (Подготовка): Снова создаем юзера (т.к. база очищается перед каждым тестом)
    client.post("/auth/register", json={"email": "chat_user2@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "chat_user2@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Создаем один чат для списка
    client.post("/conversations/", json={"title": "Чат для списка"}, headers=headers)

    # 2. Act (Действие): Запрашиваем список всех чатов
    response = client.get("/conversations/", headers=headers)

    # 3. Assert (Проверка)
    assert response.status_code == 200
    data = response.json()
    assert type(data) == list # Проверяем, что вернулся список (массив)
    assert len(data) == 1 # Проверяем, что в списке ровно 1 чат
    assert data[0]["title"] == "Чат для списка"


def test_get_conversations_invalid_token_returns_401(client):
    headers = {"Authorization": "Bearer definitely-invalid-token"}

    response = client.get("/conversations/", headers=headers)

    assert response.status_code == 401


def test_get_conversations_malformed_token_returns_401(client):
    # First JWT segment decodes to invalid UTF-8 bytes (0xd7 0xd0) and must still return 401.
    headers = {"Authorization": "Bearer 19A.xxx.xxx"}

    response = client.get("/conversations/", headers=headers)

    assert response.status_code == 401


def test_non_owner_cannot_delete_foreign_conversation(client):
    client.post("/auth/register", json={"email": "owner@example.com", "password": "123"})
    owner_login = client.post("/auth/login", data={"username": "owner@example.com", "password": "123"})
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}
    conv_resp = client.post("/conversations/", json={"title": "Owner chat"}, headers=owner_headers)
    conv_id = conv_resp.json()["id"]

    client.post("/auth/register", json={"email": "other@example.com", "password": "123"})
    other_login = client.post("/auth/login", data={"username": "other@example.com", "password": "123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    delete_resp = client.delete(f"/conversations/{conv_id}", headers=other_headers)
    assert delete_resp.status_code == 403


def test_admin_can_delete_foreign_conversation(client, db_session):
    client.post("/auth/register", json={"email": "conv_owner@example.com", "password": "123"})
    owner_login = client.post("/auth/login", data={"username": "conv_owner@example.com", "password": "123"})
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}
    conv_resp = client.post("/conversations/", json={"title": "Admin deletable"}, headers=owner_headers)
    conv_id = conv_resp.json()["id"]

    client.post("/auth/register", json={"email": "admin@example.com", "password": "123"})
    admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    admin.role = RoleEnum.admin
    db_session.commit()

    admin_login = client.post("/auth/login", data={"username": "admin@example.com", "password": "123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    delete_resp = client.delete(f"/conversations/{conv_id}", headers=admin_headers)
    assert delete_resp.status_code == 200

    get_deleted_resp = client.get(f"/conversations/{conv_id}", headers=owner_headers)
    assert get_deleted_resp.status_code == 404


