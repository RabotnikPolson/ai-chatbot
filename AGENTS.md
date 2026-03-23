# AGENTS.md

## Project Map
- Monorepo with two deployable parts: `backend/` (FastAPI + Celery + SQLAlchemy) and `frontend/` (React + Vite + Zustand + React Query).
- Runtime topology is defined in `docker-compose.yml`: `api`, `worker`, `db` (Postgres), `redis` (broker + pub/sub), `ollama` (LLM), `frontend`.
- FastAPI entrypoint is `backend/main.py`; routers are mounted from `backend/api/auth.py`, `backend/api/conversations.py` (both `router` and `messages_router`), `backend/api/admin.py`.

## Core Request/Data Flow
- Auth flow: `POST /auth/login` expects `application/x-www-form-urlencoded` (`OAuth2PasswordRequestForm`), not JSON (`backend/api/auth.py`).
- Chat send flow (`POST /conversations/{id}/messages`): persists user message + queued assistant message, accepts optional `temperature`, then enqueues Celery task `generate_reply.delay(message_id, effective_temperature)` (default `0.7`) (`backend/services/chat_service.py`, `backend/schemas/message.py`).
- Worker flow (`backend/workers/tasks.py`): marks message `processing` -> builds context from Redis/DB -> optional FAQ RAG-lite injection -> streams from Ollama -> publishes to Redis channel `chat_stream_{message_id}` -> stores final text/status in DB.
- Streaming API (`GET /messages/{message_id}/stream`) sends SSE events as full accumulated text chunks and terminates with `[DONE]`/`[ERROR]` (`backend/api/conversations.py`).
- Frontend does manual SSE parsing with `fetch`, replaces assistant message content on each chunk (no concat), aborts active streams on chat switch/unmount, auto-reconnects for `queued|processing` assistant messages after reload, then refetches canonical history on stream end (`frontend/src/pages/ChatPage.tsx`).

## State and Persistence Patterns
- DB models in `backend/db/models.py`: `User`, `Conversation`, `Message`, `FAQItem`; enum-driven statuses (`queued|processing|done|failed`) are API-visible.
- SQLAlchemy session factory in `backend/db/database.py`; Alembic env reuses `SQLALCHEMY_DATABASE_URL` from app config (`backend/alembic/env.py`).
- Frontend auth state is persisted in `auth-storage`; chat store persists only `activeConversationId` (`partialize`) in `chat-storage` (`frontend/src/store/*.ts`).
- Logout side effect clears both auth and chat state (`frontend/src/store/authStore.ts`).

## Conventions Specific to This Repo
- Service-layer pattern is real: routers are thin, business logic lives in `backend/services/*`.
- Redis is dual-purpose: Celery broker/backend and live chat transport/cache (`chat_stream_*`, `chat_partial_*`, `conversation:*:last_messages`).
- Retry semantics are message-level: `POST /messages/{id}/retry` only for assistant messages; it keeps the failed message for history and creates a new queued assistant message, then re-queues generation for the new message id (`backend/services/chat_service.py`).
- JSON structured logging is used for chat/worker latency and status (`backend/services/logger.py`).

## Developer Workflows (Confirmed from repo)
- Start stack: `docker compose up --build -d` (root `README.md`).
- Apply migrations: `docker compose exec api alembic upgrade head`.
- Pull/test model in Ollama: `docker compose exec ollama ollama run qwen2.5:0.5b`.
- Backend tests: `docker compose exec api pytest` (or target `backend/tests/`).
- Lint/format hooks are pre-commit based (`.pre-commit-config.yaml`): Ruff + Ruff format for Python, Prettier for frontend assets.
- Run all configured hooks manually with `pre-commit run --all-files` (root `README.md`).

## Testing Realities
- API tests use in-memory SQLite with dependency override for `get_db` (`backend/tests/conftest.py`); this differs from production Postgres.
- Message tests mock both Celery dispatch and Redis calls, assert temperature pass-through to Celery, and cover retry behavior that creates a new assistant message (`backend/tests/test_messages.py`).
- Worker test checks idempotency when message is already `done` (`backend/tests/test_worker.py`).

## Integration Boundaries
- External dependencies to keep in mind: Postgres, Redis, Ollama HTTP API (`http://ollama:11434/api/chat`), JWT secret via `SECRET_KEY` env.
- Frontend API base URL is hardcoded to `http://localhost:8000/` in `frontend/src/api/axios.ts` (not env-driven yet).
- CORS currently allows `http://localhost:5173` and `http://127.0.0.1:5173` (`backend/main.py`).
- Health check endpoint `GET /health` validates DB (`SELECT 1`) and Redis (`PING`), returning `503` when any dependency is unhealthy (`backend/main.py`).
