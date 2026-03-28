def test_register_user_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data


def test_login_user_success(client):
    client.post(
        "/auth/register",
        json={"email": "login_test@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/login",
        data={"username": "login_test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"