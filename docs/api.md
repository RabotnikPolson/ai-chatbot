# API Reference

## Base URL
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Как работать с авторизацией

Почти все методы требуют JWT токен в заголовке:

```http
Authorization: Bearer <access_token>
```

Без токена можно вызывать:
- `POST /auth/register`
- `POST /auth/login`
- `GET /health`
- `GET /` (корневой пинг)

---

## Auth Endpoints

### POST /auth/register
Создает нового пользователя.

**Отправить (JSON):**
```json
{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Успех (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2026-03-27T10:00:00Z"
}
```

**Ошибки:**
- `400` - email уже занят

### POST /auth/login
Логин и получение токенов.

Важно: тут нужен **form-data** (`application/x-www-form-urlencoded`), не JSON.

**Отправить:**
```http
username=user@example.com&password=strongpassword123
```

**Успех (200):**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

**Ошибки:**
- `400` - неверный email или пароль

### POST /auth/refresh
Выдает новый access token по refresh token.

**Отправить (JSON):**
```json
{
  "refresh_token": "..."
}
```

**Успех (200):**
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

**Ошибки:**
- `401` - refresh токен невалидный или просрочен

### GET /auth/me
Технический endpoint для проверки, что токен читается.

**Успех (200):**
```json
{
  "message": "VALAR MARGULIS!",
  "your_token": "<токен из заголовка>"
}
```

---

## Conversation Endpoints

### POST /conversations/
Создает новый диалог.

**Отправить (JSON):**
```json
{
  "title": "Мой чат"
}
```

`title` можно не передавать (будет `null`).

### GET /conversations/
Возвращает список ваших диалогов.

**Параметры:**
- `page` (по умолчанию `1`)
- `limit` (по умолчанию `20`)

### GET /conversations/{id}
Возвращает один диалог по id.

**Ошибки:**
- `404` - диалог не найден или нет доступа

### GET /conversations/{conversation_id}/messages
Возвращает историю сообщений в диалоге (по времени создания).

### POST /conversations/{conversation_id}/messages
Отправляет пользовательский текст и запускает генерацию ответа ассистента.

**Отправить (JSON):**
```json
{
  "text": "Привет!",
  "temperature": 0.5
}
```

`temperature` необязателен, по умолчанию `0.7`.

**Успех (200):**
```json
{
  "message_id": "4d4a0f5d-cba9-4888-9c3d-e7f29f7dc4f6",
  "status": "queued"
}
```

Что происходит внутри:
1. Сообщение пользователя сохраняется как `done`.
2. Создается сообщение ассистента как `queued`.
3. В Celery ставится задача генерации.

### DELETE /conversations/{id}
Удаляет диалог.

Кто может удалить:
- владелец диалога
- админ

**Успех (200):**
```json
{
  "message": "Диалог удален"
}
```

**Ошибки:**
- `403` - нет прав
- `404` - диалог не найден

---

## Message Endpoints

### GET /messages/{message_id}
Возвращает одно сообщение по UUID.

### GET /messages/{message_id}/stream
SSE-стрим для ответа ассистента.

**Как это работает:**
1. Если сообщение уже `done`, сервер сразу шлет `data: [DONE]`.
2. Если еще генерируется, сервер слушает Redis-канал `chat_stream_{message_id}`.
3. Во время генерации приходят `data: ...` (весь накопленный текст).
4. Финал: `data: [DONE]` или `data: [ERROR]`.

**Пример ответа:**
```text
data: "Привет"

data: "Привет, чем помочь?"

data: [DONE]
```

### POST /messages/{message_id}/retry
Повторная генерация для неудачного ответа ассистента.

Важно:
- работает только для `assistant` + `status=failed`
- старое сообщение остается в истории
- создается новое сообщение со статусом `queued`
- новая задача запускается с `temperature=0.7`

**Ошибки:**
- `400` - нельзя повторить это сообщение
- `403` - сообщение не из вашего диалога
- `404` - сообщение не найдено

---

## Admin Endpoints

Все методы ниже только для роли `admin`.

### POST /admin/faq/
Создает FAQ запись.

**Отправить (JSON):**
```json
{
  "title": "Как оформить возврат?",
  "content": "Возврат возможен в течение 30 дней.",
  "tags": "policy,returns"
}
```

### GET /admin/faq/
Возвращает все FAQ записи.

### DELETE /admin/faq/{id}
Удаляет FAQ запись.

**Ошибки:**
- `403` - пользователь не админ
- `404` - FAQ не найден

---

## System Endpoints

### GET /health
Проверяет подключение к БД и Redis.

**Успех (200):**
```json
{
  "status": "all systems go",
  "details": {
    "db": "ok",
    "redis": "ok"
  }
}
```

**Ошибка (503):**
```json
{
  "detail": {
    "db": "error: ...",
    "redis": "ok"
  }
}
```

---

## Data Types (коротко)

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2026-03-27T10:00:00Z"
}
```

### Conversation
```json
{
  "id": 42,
  "owner_user_id": 1,
  "title": "Мой чат",
  "created_at": "2026-03-27T10:00:00Z"
}
```

### Message
```json
{
  "id": "4d4a0f5d-cba9-4888-9c3d-e7f29f7dc4f6",
  "conversation_id": 42,
  "role": "assistant",
  "content": "Готово",
  "status": "done",
  "provider": "ollama",
  "latency_ms": 1234,
  "error": null,
  "created_at": "2026-03-27T10:00:05Z"
}
```

### FAQItem
```json
{
  "id": 1,
  "title": "Как оформить возврат?",
  "content": "Возврат возможен в течение 30 дней.",
  "tags": "policy,returns",
  "updated_at": "2026-03-27T10:00:00Z"
}
```

---

## Error Responses

Ошибки приходят в поле `detail`:

```json
{
  "detail": "Неверный email или пароль"
}
```

Частые коды:
- `200` - успешно
- `400` - некорректный запрос
- `401` - токен невалидный/просроченный
- `403` - доступ запрещен
- `404` - объект не найден
- `503` - проблема с зависимостями (БД/Redis)

