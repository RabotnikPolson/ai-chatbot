# Architecture

## System Overview

AI ChatBot is a monorepo application with FastAPI backend and React frontend. The system follows a clear separation of concerns with async task processing via Celery and Redis for real-time communication.

## Component Architecture

### Frontend (React + TypeScript + Vite)
- **Pages:**
  - `LoginPage` — authentication and registration
  - `ChatPage` — main chat interface with message display and input
  - `Layout` — sidebar with conversation list and navigation
- **State Management:**
  - `authStore` (Zustand) — user session, tokens
  - `chatStore` (Zustand) — conversations, active conversation ID
- **API Client:**
  - Axios with Bearer token injection
  - Automatic token refresh on 401

### Backend (FastAPI + Pydantic v2)

#### Routers (API Layer)
- `api/auth.py` — login, register, token refresh
- `api/conversations.py` — CRUD for conversations and messages, SSE streaming
- `api/admin.py` — FAQ management (admin only)

#### Services (Business Logic)
- `services/chat_service.py` — conversation/message operations, task enqueueing
- `services/auth_service.py` — user registration, authentication, token generation
- `services/security.py` — password hashing, JWT creation/validation
- `services/logger.py` — JSON structured logging

#### Providers (External Integrations)
- `providers/ollama.py` — OllamaProvider for LLM calls with streaming

#### Database (SQLAlchemy ORM)
- `db/models.py` — User, Conversation, Message, FAQItem tables
- `db/database.py` — session factory, database URL configuration

#### Workers (Celery Async Tasks)
- `workers/tasks.py` — `generate_reply()` task: processes message generation
- `workers/celery_app.py` — Celery app initialization with Redis broker

### Infrastructure
- **Database:** PostgreSQL (prod) / SQLite (tests)
- **Cache & Broker:** Redis
- **LLM:** Ollama (local HTTP API)
- **Task Queue:** Celery + Redis

## Data Flow

### Send Message Flow
```
1. User sends message (ChatPage UI)
   ↓
2. POST /conversations/{id}/messages
   ↓
3. ChatService.send_message()
   - Save user message (status: done)
   - Create assistant message (status: queued)
   - Update Redis cache (conversation:{id}:last_messages)
   - Enqueue Celery task: generate_reply(message_id, temperature)
   - Return {message_id, status}
   ↓
4. Response sent to frontend immediately
   ↓
5. Frontend polls GET /messages/{id} or streams GET /messages/{id}/stream
```

### Worker Generation Flow
```
1. Celery task: generate_reply(message_id, temperature)
   ↓
2. Mark message status: processing
   ↓
3. Fetch conversation context:
   - Try Redis cache (conversation:{id}:last_messages)
   - On miss: query last 20 done messages from DB
   ↓
4. RAG-lite injection:
   - Find system FAQ (role, tone)
   - Find relevant FAQ (keyword search on user query)
   - Build system prompt with FAQ context
   ↓
5. Stream from Ollama:
   - Each chunk published to Redis channel (chat_stream_{id})
   - Full accumulated text stored in (chat_partial_{id})
   - Full answer concatenated locally
   ↓
6. Save to DB:
   - message.content = full_answer
   - message.status = done
   - message.latency_ms = elapsed_ms
   ↓
7. Publish [DONE] signal to Redis channel
   ↓
8. Frontend receives stream events and updates UI
```

### Streaming API Flow
```
1. Frontend subscribes: GET /messages/{message_id}/stream
   ↓
2. Backend:
   - If message.status == done: return [DONE] immediately
   - Else: subscribe to Redis channel (chat_stream_{message_id})
   ↓
3. Server-Sent Events (SSE):
   - Each Redis publish → SSE data event
   - Frontend parses accumulated text (not concatenated)
   - Terminal event: [DONE] or [ERROR]
   ↓
4. Frontend refetches full history on stream end
```

## State Persistence

### Database
- **Users:** email, hashed_password, role (user|admin)
- **Conversations:** owner_user_id, title, created_at
- **Messages:** conversation_id, role (user|assistant), content, status (queued|processing|done|failed), provider, latency_ms, error
- **FAQItems:** title, content, tags

### Redis
- **Cache:** `conversation:{id}:last_messages` (JSON history, TTL 60s)
- **Streams:** `chat_stream_{message_id}` (Pub/Sub channel for SSE)
- **Partial:** `chat_partial_{message_id}` (accumulated text for reconnect, TTL 3600s)

### Frontend (LocalStorage)
- **auth-storage:** `token`, `refreshToken`, `isAuthenticated`
- **chat-storage:** `activeConversationId` (partialize strategy)

## Message Lifecycle

```
User Creates Message
  ↓
user_message: status=done (saved immediately)
assistant_message: status=queued (empty, awaiting generation)
  ↓
[Worker picks up task]
  ↓
assistant_message: status=processing
  ↓
[Stream generation + publish to Redis]
  ↓
assistant_message: status=done, content=full_text, latency_ms=N
  ↓
[SSE stream terminates]
  ↓
Frontend refetches and displays final state
```

## Error Handling & Resilience

### Message Generation Failures
- Task retries up to 3 times with exponential backoff
- On final failure: message.status=failed, message.error=str(exception)
- SSE stream sends [ERROR] signal to frontend
- User sees "Ошибка" badge + "Retry" button

### Retry Semantics
- `POST /messages/{id}/retry` creates new assistant message (NOT updating old one)
- Old failed message preserved for audit trail
- New message re-enqueued with default temperature 0.7

### Health Check
- `GET /health` validates DB (SELECT 1) and Redis (PING)
- Returns 503 if any dependency unhealthy

## Security

- **Auth:** JWT (HS256) with 30-min access token, 7-day refresh token
- **CORS:** Allows localhost:5173 and 127.0.0.1:5173
- **Passwords:** bcrypt hashing (passlib)
- **Admin:** Role-based access for FAQ management
- **Ownership:** Conversations belong to users; non-owners require admin for deletion

## Logging

- **JSON structured logs:** timestamp, level, message, custom_fields
- **Fields tracked:** request_id, user_id, conversation_id, message_id, status, latency_ms
- **Logger names:** chat_service_logger, worker_logger
- **Output:** stderr (StreamHandler)

