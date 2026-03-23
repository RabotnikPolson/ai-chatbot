# API Reference

## Base URL
- **Development:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`

## Authentication

All endpoints except `/auth/register`, `/auth/login`, `/health` require Bearer token in `Authorization` header:
```
Authorization: Bearer <access_token>
```

Tokens are short-lived (30 min access, 7 day refresh). Use `/auth/refresh` to renew.

---

## Auth Endpoints

### POST /auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2026-03-23T10:00:00Z"
}
```

**Errors:**
- `400` — Email already registered

---

### POST /auth/login
Authenticate and obtain tokens.

**Request:** Form-encoded (not JSON!)
```
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors:**
- `400` — Invalid email or password

---

### POST /auth/refresh
Renew access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` — Refresh token expired or invalid

---

## Conversation Endpoints

### POST /conversations
Create a new conversation.

**Request:**
```json
{
  "title": "My Chat"
}
```

**Response (200):**
```json
{
  "id": 42,
  "owner_user_id": 1,
  "title": "My Chat",
  "created_at": "2026-03-23T10:00:00Z"
}
```

---

### GET /conversations
List user's conversations (paginated).

**Query Parameters:**
- `page` (optional, default 1): Page number
- `limit` (optional, default 20): Items per page

**Response (200):**
```json
[
  {
    "id": 42,
    "owner_user_id": 1,
    "title": "My Chat",
    "created_at": "2026-03-23T10:00:00Z"
  }
]
```

---

### GET /conversations/{id}
Fetch a single conversation.

**Response (200):**
```json
{
  "id": 42,
  "owner_user_id": 1,
  "title": "My Chat",
  "created_at": "2026-03-23T10:00:00Z"
}
```

**Errors:**
- `404` — Conversation not found or access denied

---

### GET /conversations/{conversation_id}/messages
Fetch all messages in a conversation (ordered by creation time).

**Response (200):**
```json
[
  {
    "id": 1,
    "conversation_id": 42,
    "role": "user",
    "content": "Hello!",
    "status": "done",
    "provider": null,
    "latency_ms": null,
    "error": null,
    "created_at": "2026-03-23T10:00:00Z"
  },
  {
    "id": 2,
    "conversation_id": 42,
    "role": "assistant",
    "content": "Hi there!",
    "status": "done",
    "provider": "ollama",
    "latency_ms": 2340,
    "error": null,
    "created_at": "2026-03-23T10:00:05Z"
  }
]
```

---

### POST /conversations/{conversation_id}/messages
Send a message and enqueue bot response generation.

**Request:**
```json
{
  "text": "What is the capital of France?",
  "temperature": 0.5
}
```

**Fields:**
- `text` (required): User message
- `temperature` (optional, default 0.7): LLM temperature (0.0 - 1.0, lower = more deterministic)

**Response (200):**
```json
{
  "message_id": 2,
  "status": "queued"
}
```

**Details:**
- User message is saved immediately with `status: done`
- Assistant message created with `status: queued`
- Celery task enqueued: `generate_reply(message_id=2, temperature=0.5)`
- Use `/messages/{message_id}/stream` to follow generation

**Errors:**
- `404` — Conversation not found or access denied

---

### DELETE /conversations/{id}
Delete a conversation (owner or admin only).

**Response (200):**
```json
{
  "message": "Диалог удален"
}
```

**Errors:**
- `403` — Access denied (not owner and not admin)
- `404` — Conversation not found

---

## Message Endpoints

### GET /messages/{message_id}
Get a single message's status and content.

**Response (200):**
```json
{
  "id": 2,
  "conversation_id": 42,
  "role": "assistant",
  "content": "Hi there!",
  "status": "done",
  "provider": "ollama",
  "latency_ms": 2340,
  "error": null,
  "created_at": "2026-03-23T10:00:05Z"
}
```

**Statuses:**
- `queued` — Waiting in task queue
- `processing` — Worker is generating
- `done` — Generation complete
- `failed` — Generation failed; see `error` field

**Errors:**
- `404` — Message not found or access denied

---

### GET /messages/{message_id}/stream
Stream message generation as Server-Sent Events (SSE).

**Response:**
```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache

data: "This is "
data: "This is a "
data: "This is a test"
data: [DONE]
```

**Behavior:**
1. If message.status == `done`: immediately send `[DONE]`
2. Else: subscribe to Redis channel `chat_stream_{message_id}`
3. Each chunk received from worker → `data: <accumulated_full_text>`
4. Terminal event: `[DONE]` (success) or `[ERROR]` (worker failure)

**Frontend Parsing:**
```javascript
const response = await fetch('http://localhost:8000/messages/2/stream');
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = decoder.decode(value);
  const lines = text.split('\n\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const payload = line.slice(6);
      if (payload === '[DONE]') {
        console.log('Stream ended');
        break;
      } else {
        console.log('Chunk:', JSON.parse(payload));
      }
    }
  }
}
```

**Errors:**
- `404` — Message not found or access denied

---

### POST /messages/{message_id}/retry
Retry a failed assistant message (creates new message).

**Response (200):**
```json
{
  "id": 3,
  "conversation_id": 42,
  "role": "assistant",
  "content": "",
  "status": "queued",
  "provider": "ollama",
  "latency_ms": null,
  "error": null,
  "created_at": "2026-03-23T10:00:10Z"
}
```

**Behavior:**
- Only works for `status: failed` messages
- Old message preserved for history
- New message created with `status: queued` and fresh `id`
- New Celery task enqueued with default `temperature: 0.7`

**Errors:**
- `400` — Message is not an assistant message or not failed
- `404` — Message not found or access denied

---

## Admin Endpoints

All admin endpoints require `role: admin`.

### POST /admin/faq
Create a new FAQ item.

**Request:**
```json
{
  "title": "What is our return policy?",
  "content": "Returns accepted within 30 days of purchase.",
  "tags": "policy,returns"
}
```

**Response (200):**
```json
{
  "id": 1,
  "title": "What is our return policy?",
  "content": "Returns accepted within 30 days of purchase.",
  "tags": "policy,returns",
  "updated_at": "2026-03-23T10:00:00Z"
}
```

**Errors:**
- `403` — User is not admin

---

### GET /admin/faq
List all FAQ items.

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "What is our return policy?",
    "content": "Returns accepted within 30 days of purchase.",
    "tags": "policy,returns",
    "updated_at": "2026-03-23T10:00:00Z"
  }
]
```

**Errors:**
- `403` — User is not admin

---

### DELETE /admin/faq/{id}
Delete an FAQ item.

**Response (200):**
```json
{
  "message": "FAQ deleted."
}
```

**Errors:**
- `403` — User is not admin
- `404` — FAQ not found

---

## System Endpoints

### GET /health
Health check: validates DB and Redis connectivity.

**Response (200):**
```json
{
  "status": "all systems go",
  "details": {
    "db": "ok",
    "redis": "ok"
  }
}
```

**Response (503):** If any dependency is down
```json
{
  "detail": {
    "db": "error: connection refused",
    "redis": "ok"
  }
}
```

---

## Data Types (Pydantic Models)

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2026-03-23T10:00:00Z"
}
```

### Conversation
```json
{
  "id": 42,
  "owner_user_id": 1,
  "title": "My Chat",
  "created_at": "2026-03-23T10:00:00Z"
}
```

### Message
```json
{
  "id": 2,
  "conversation_id": 42,
  "role": "assistant",
  "content": "Hi there!",
  "status": "done",
  "provider": "ollama",
  "latency_ms": 2340,
  "error": null,
  "created_at": "2026-03-23T10:00:05Z"
}
```

### FAQItem
```json
{
  "id": 1,
  "title": "What is our return policy?",
  "content": "Returns accepted within 30 days of purchase.",
  "tags": "policy,returns",
  "updated_at": "2026-03-23T10:00:00Z"
}
```

---

## Error Responses

All errors return JSON with `detail` field:

```json
{
  "detail": "Неверный логин или пароль"
}
```

Common HTTP status codes:
- `200` — Success
- `400` — Bad request (invalid input)
- `401` — Unauthorized (invalid/expired token)
- `403` — Forbidden (access denied)
- `404` — Not found
- `503` — Service unavailable (DB/Redis down)

