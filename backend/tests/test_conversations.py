# tests/test_conversations.py

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