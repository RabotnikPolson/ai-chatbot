# test_auth.py

def test_register_user_success(client):
    # 1. Act (Действие): Отправляем POST запрос на регистрацию
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )

    # 2. Assert (Проверки):
    # Проверяем, что сервер ответил "200 OK"
    assert response.status_code == 200

    # Получаем ответ в виде словаря (JSON)
    data = response.json()

    # Проверяем, что в ответе вернулся правильный email
    assert data["email"] == "test@example.com"
    # Проверяем, что сервер выдал нам ID (он не должен быть пустым)
    assert "id" in data
    # Проверяем, что пароль НЕ вернулся в открытом виде (безопасность!)
    assert "password" not in data


def test_login_user_success(client):
    # 1. Сначала регистрируем юзера (Arrange)
    client.post(
        "/auth/register",
        json={"email": "login_test@example.com", "password": "password123"}
    )

    # 2. Теперь пытаемся залогиниться (Act)
    # Обрати внимание: эндпоинт логина ждет данные в формате Form (x-www-form-urlencoded),
    # а не JSON, потому что мы используем OAuth2PasswordRequestForm
    response = client.post(
        "/auth/login",
        data={"username": "login_test@example.com", "password": "password123"}
    )

    # 3. Проверяем результат (Assert)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"