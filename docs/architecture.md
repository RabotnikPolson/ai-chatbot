# Architecture

## System Overview

AI ChatBot - это один репозиторий с двумя частями:
- backend на FastAPI
- frontend на React

Главная идея простая: API быстро принимает сообщение, а тяжелую генерацию ответа делает воркер в фоне через Celery. Redis тут нужен и как очередь, и как канал для онлайн-стрима ответа.

## Component Architecture

### Frontend (React + TypeScript + Vite)
- **Pages:**
  - `LoginPage` - вход и регистрация
  - `ChatPage` - сам чат (сообщения, ввод, стрим)
  - `Layout` - боковая панель со списком диалогов
- **State Management:**
  - `authStore` (Zustand) - токены и статус авторизации
  - `chatStore` (Zustand) - список чатов и активный чат
- **API Client:**
  - Axios автоматически подставляет Bearer токен
  - Если пришел `401`, frontend пробует обновить токен через `/auth/refresh`

### Backend (FastAPI + Pydantic v2)

#### Routers (API Layer)
- `api/auth.py` - регистрация, логин, refresh токена
- `api/conversations.py` - чаты, сообщения, SSE-стрим
- `api/admin.py` - FAQ для админа

#### Services (Business Logic)
- `services/chat_service.py` - логика чатов/сообщений и постановка задач в очередь
- `services/auth_service.py` - логика регистрации и входа
- `services/security.py` - хэширование паролей и JWT
- `services/logger.py` - JSON-логи

#### Providers (External Integrations)
- `providers/ollama.py` - клиент к Ollama (получение ответа модели)

#### Database (SQLAlchemy ORM)
- `db/models.py` - таблицы `User`, `Conversation`, `Message`, `FAQItem`
- `db/database.py` - подключение к БД и сессии

#### Workers (Celery Async Tasks)
- `workers/tasks.py` - задача `generate_reply()`, которая генерирует ответ
- `workers/celery_app.py` - настройка Celery

### Infrastructure
- **Database:** PostgreSQL в рантайме, SQLite в тестах
- **Cache & Broker:** Redis
- **LLM:** Ollama по HTTP
- **Task Queue:** Celery + Redis

## Data Flow

### Send Message Flow
```
1. Пользователь отправляет текст в `ChatPage`
   ↓
2. Frontend вызывает POST /conversations/{id}/messages
   ↓
3. В `ChatService.send_message()`:
   - сохраняется сообщение пользователя (status=done)
   - создается пустой ответ ассистента (status=queued)
   - обновляется кэш истории в Redis (conversation:{id}:last_messages)
   - ставится Celery-задача generate_reply(message_id, temperature)
   - сразу возвращается {message_id, status}
   ↓
4. Frontend сразу получает ответ API
   ↓
5. Frontend получает генерацию через GET /messages/{id}/stream
```

### Worker Generation Flow
```
1. Воркер запускает generate_reply(message_id, temperature)
   ↓
2. Сообщение переводится в status=processing
   ↓
3. Собирается контекст:
   - сначала попытка взять историю из Redis
   - если кэша нет, берутся последние done-сообщения из БД
   ↓
4. Добавляется FAQ-контекст (RAG-lite):
   - системные FAQ (тон/роль/правила)
   - релевантные FAQ по словам из запроса
   ↓
5. Идет поток от Ollama:
   - накопленный текст публикуется в `chat_stream_{id}`
   - тот же накопленный текст кладется в `chat_partial_{id}`
   ↓
6. В Redis публикуется финальный маркер `[DONE]`
   ↓
7. В БД сохраняется итог:
   - `message.content = full_answer`
   - `message.status = done`
   - `message.latency_ms = время генерации`
```

### Streaming API Flow
```
1. Frontend открывает GET /messages/{message_id}/stream
   ↓
2. Backend проверяет статус:
   - если уже done -> сразу отдает [DONE]
   - иначе подписывается на Redis-канал chat_stream_{message_id}
   ↓
3. По мере генерации backend шлет SSE-события:
   - payload это весь накопленный текст на текущий момент
   - финал: [DONE] или [ERROR]
   ↓
4. После завершения frontend заново запрашивает историю из БД
```

## State Persistence

### Database
- **Users:** `email`, `password_hash`, `role` (`user|admin`)
- **Conversations:** владелец, заголовок, дата создания
- **Messages:** роль, текст, статус (`queued|processing|done|failed`), провайдер, latency, ошибка
- **FAQItems:** заголовок, контент, теги

### Redis
- **Cache:** `conversation:{id}:last_messages` (история чата, TTL 180 секунд)
- **Streams:** `chat_stream_{message_id}` (канал стрима)
- **Partial:** `chat_partial_{message_id}` (накопленный текст для переподключения, TTL 3600 секунд)

### Frontend (LocalStorage)
- **auth-storage:** `token`, `refreshToken`, `isAuthenticated`
- **chat-storage:** хранится только `activeConversationId`

## Message Lifecycle

```
Пользователь отправил сообщение
  ↓
user_message: done
assistant_message: queued
  ↓
Воркер взял задачу
  ↓
assistant_message: processing
  ↓
Генерация + стрим в Redis
  ↓
assistant_message: done + финальный текст + latency
  ↓
Frontend перезапрашивает историю и показывает итог
```

## Error Handling & Resilience

### Message Generation Failures
- Воркер делает до 3 retry при сетевых ошибках
- Если не удалось: `status=failed`, текст ошибки кладется в `message.error`
- В SSE уходит `[ERROR]`
- В UI видно статус ошибки и кнопку повтора

### Retry Semantics
- `POST /messages/{id}/retry` не перезаписывает старое сообщение
- Создается новое assistant-сообщение со статусом `queued`
- Старое failed-сообщение остается в истории

### Health Check
- `GET /health` проверяет БД (`SELECT 1`) и Redis (`PING`)
- Если что-то не работает, API возвращает `503`

## Security

- **Auth:** JWT (`HS256`), access token на 30 минут, refresh на 7 дней
- **CORS:** разрешены `http://localhost:5173` и `http://127.0.0.1:5173`
- **Passwords:** bcrypt (через passlib)
- **Admin:** FAQ API доступно только роли admin
- **Ownership:** удалять чужой диалог может только admin

## Logging

- Логи в JSON (удобно фильтровать и искать)
- Основные поля: `request_id`, `user_id`, `conversation_id`, `message_id`, `status`, `latency_ms`
- Используются логгеры: `chat_service_logger`, `worker_logger`

