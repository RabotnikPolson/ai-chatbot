from db.models import User, RoleEnum

def test_create_conversation(client):
    client.post("/auth/register", json={"email": "chat_user@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "chat_user@example.com", "password": "123"})
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/conversations/", json={"title": "My first test chat"}, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My first test chat"
    assert "id" in data

def test_get_conversations(client):
    client.post("/auth/register", json={"email": "chat_user2@example.com", "password": "123"})
    login_resp = client.post("/auth/login", data={"username": "chat_user2@example.com", "password": "123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/conversations/", json={"title": "List test chat"}, headers=headers)

    response = client.get("/conversations/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert type(data) == list
    assert len(data) == 1
    assert data[0]["title"] == "List test chat"


def test_get_conversations_invalid_token_returns_401(client):
    headers = {"Authorization": "Bearer definitely-invalid-token"}

    response = client.get("/conversations/", headers=headers)

    assert response.status_code == 401


def test_get_conversations_malformed_token_returns_401(client):
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


