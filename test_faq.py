import requests
import time

BASE_URL = "http://localhost:8000"
EMAIL = "test_verification@example.com"
PASSWORD = "password123"

def run_test():
    # 1. Register
    try:
        requests.post(f"{BASE_URL}/auth/register", json={"email": EMAIL, "password": PASSWORD})
        print("Registered user")
    except:
        pass

    # 2. Login
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create conversation
    resp = requests.post(f"{BASE_URL}/conversations/", headers=headers, json={"title": "Verification Chat"})
    conv_id = resp.json()["id"]
    print(f"Created conversation {conv_id}")

    # 4. Send message
    # Use Russian as per FAQ context
    resp = requests.post(f"{BASE_URL}/conversations/{conv_id}/messages", headers=headers, json={"text": "Привет, кто ты?"})
    msg_id = resp.json()["id"]
    print(f"Sent message, assistant message id: {msg_id}")

    # 5. Wait for worker
    print("Waiting for worker to process...")
    time.sleep(5)

if __name__ == "__main__":
    run_test()
