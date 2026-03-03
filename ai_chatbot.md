# AI ChatBot

## Цель: Сделать рабочее веб-приложение чат-бот помощник:

- есть логин (JWT + refresh)
- есть список диалогов
- можно писать сообщения
- ответ бота генерируется локально через Ollama (без платных API)
- генерация ответа идёт через очередь/воркер, не в HTTP-запросе
- всё поднимается локально одной командой через docker-compose

## Что должно уметь приложение (пользовательский сценарий)

- Пользователь логинится
- Создаёт диалог
- Пишет сообщение
- Сообщение сразу появляется в UI со статусом queued/processing
- Через несколько секунд появляется ответ бота со статусом done
- Если генерация упала — статус failed, показывается ошибка и кнопка “Retry” (повторная отправка)

Ограничения

- AWS не используем в реализации (будет отдельный теоретический файл в конце).
- Платные LLM API запрещены. Основная генерация — только через Ollama локально.
- Никаких ключей/секретов в репозитории.

## Технологии

- Frontend: React или Next.js + TypeScript
- Backend: FastAPI + Pydantic v2
- DB: Postgres
- Redis: кэш + брокер очереди
- Worker: Celery (предпочтительно)
- LLM: Ollama (docker) + модель (например qwen/deepseek-совместимая)
- Всё запускается: docker-compose

## Архитектурные правила (обязательные)

- HTTP-эндпоинт не вызывает LLM напрямую. Он только:
    - пишет данные в БД;
    - ставит задачу в очередь;
    - отдаёт message_id;
- Вся логика генерации — в воркере (generate_reply(message_id)).
- Должен быть отдельный слой сервисов и провайдеров, чтобы код не был в одном файле.

## Рекомендуемая структура проекта backend:

- api/ - роуты
- services/ - бизнес-логика чата
- providers/ - LLM провайдеры (Ollama)
- db/ - модели, сессии, миграции
- workers/ - celery tasks
- schemas/ - DTO  

## Минимум таблиц:

- users
    - id    
    - email
    - password_hash
    - role = admin|user
    - created_at

- conversations
    - id
    - owner_user_id
    - title (nullable)
    - created_at

- messages
    - id
    - conversation_id
    - role = user|assistant
    - content
    - status = queued|processing|done|failed
    - created_at
    - provider = ollama
    - latency_ms (nullable)
    - error (nullable)
    - created_at

- faq_items (для RAG-lite)
    - id
    - title
    - content
    - tags (nullable)
    - updated_at

## API контракт (минимум)
- Auth
    - POST /auth/login → {access_token, refresh_token}
    - POST /auth/refresh → новый access_token
- Conversations
    - POST /conversations → создать диалог
    - GET /conversations?page=&limit= → список
    - GET /conversations/{id} → детали + сообщения (можно отдельным методом)
    - DELETE /conversations/{id} → удалить (owner или admin)
- Messages
    - POST /conversations/{id}/messages → отправить сообщение
        - input: { text: string, temperature?: number }
        - output: { message_id: uuid, status: "queued" }
    - GET /messages/{message_id} → статус + ответ
        - output: { status, answer?, error?, provider?, latency_ms? }
    - (опционально) GET /messages/{message_id}/stream (SSE)

## Очередь и воркер (обязательно)

- Поведение POST /messages
    - сохранить user-сообщение в БД
    - создать “пустое” assistant-сообщение со статусом queued
    - отправить задачу воркеру: generate_reply(assistant_message_id)
- Поведение воркера generate_reply(message_id)
    - выставить статус processing
    - собрать контекст диалога (последние N=20 сообщений)
    - подтянуть релевантные FAQ (см. RAG-lite)
    - вызвать OllamaProvider
    - записать ответ, latency, provider
    - поставить done
- Надёжность
    - таймаут на вызов Ollama (например 60s)
    - retry с backoff на сетевые ошибки
    - idempotency: если статус уже done — задача ничего не делает (не создаёт дубль)

## LLM через Ollama (обязательно)

- реализовать OllamaProvider:
    - один метод: generate(messages, temperature) -> text
    - ограничения:
        - max длина user text (например 8000 символов)
        - max количество сообщений контекста (например 20)
    - логировать:
        - время ответа
        - ошибки/таймауты

## RAG-lite (обязательно, простая версия)

Цель: чтобы бот использовал “знания компании” из FAQ.

Как работает:

- при генерации ответа воркер ищет 3–5 FAQ, релевантных запросу пользователя допустимо:
    - Postgres full-text
    - или простой ILIKE по title/content (для MVP)

- добавляет найденные FAQ фрагменты в prompt как “Контекст” 

Админ API для FAQ:

- POST /admin/faq (только admin)
- GET /admin/faq

Важно:

- полный prompt не сохранять в БД
- можно логировать “какие FAQ id были выбраны”

## Кэширование Redis (обязательно)

Реализовать минимум один кейс:
- кэш последних сообщений диалога: conversation:{id}:last_messages TTL 60–120s
- при добавлении сообщения — обновлять/инвалидировать кэш
- в логах показать попадание/промах кэша

## Frontend (обязательно)

Экраны:
- Login
- Список диалогов
- Диалог (чат)
Функции UI:
- отправка сообщения
- отображение статусов queued/processing/done/failed
- retry на failed (создаёт новое сообщение)
- нормальные состояния: loading / empty / error
Технически:
- TS типы для DTO
- React Query/SWR для запросов

## Наблюдаемость и эксплуатация (обязательно)

- JSON-логи backend и worker
- поля минимум: request_id, user_id, conversation_id, message_id, status, latency_ms
- GET /health проверяет:
    - DB доступна
    - Redis доступен
    - (опционально) Ollama доступна

## Качество и тесты (обязательно)

- линтер/форматтер (pre-commit или отдельные команды)
- минимально 8 тестов:
    - auth (1–2)
    - conversations CRUD (2)
    - messages flow (2)
    - unit test для OllamaProvider через mock (1–2)
    - тест idempotency воркера (1)

## Запуск проекта (обязательно)

В корне должен быть docker-compose.yml с сервисами:

- frontend
- api
- worker
- postgres
- redis
- ollama

## README должен содержать:

- docker compose up --build
- как применить миграции
- как запустить тесты
- как скачать/загрузить модель в Ollama и проверить, что она отвечает

Критерий: новый человек поднимает проект по README без дополнительных объяснений.

Что сдавать (артефакты)

- Репозиторий (mono-repo): /frontend, /backend, /docs
- Рабочий запуск через compose
- Документы:
    - /docs/architecture.md — схема потоков (send_message → queue → worker → db → UI)
    - /docs/decisions.md — почему так сделано (очередь, кэш, ретраи)
    - /docs/api.md — список эндпоинтов и примеры DTO

## План выполнения (4 спринта)

Спринт 1: skeleton + auth + conversations (без LLM)
Спринт 2: messages + очередь/воркер (пока заглушка ответа)
Спринт 3: OllamaProvider + реальная генерация + статусы
Спринт 4: RAG-lite + кэш + тесты + доки + полировка

## Чеклист приёмки

- всё поднимается через docker-compose
- LLM локально через Ollama, без внешних API
- генерация ответа идёт через воркер/очередь
- есть RAG-lite (FAQ) и кэш Redis
- есть health, логи, тесты, документация
