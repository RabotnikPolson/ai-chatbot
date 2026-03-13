# AI-Chatbot Project

This is the backend and soon-to-be frontend for the AI Chatbot application.

## Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)

## Как запустить проект (Быстрый старт)

1. Клонируйте репозиторий.
2. Соберите и запустите все контейнеры одной командой:
   ```bash
   docker compose up --build -d
   ```
3. **Как применить миграции базы данных:**
   ```bash
   docker compose exec api alembic upgrade head
   ```
4. **Как скачать/загрузить модель в Ollama и проверить:**
   ```bash
   docker compose exec ollama ollama run qwen2.5:0.5b
   ```
   *Вы можете задать боту любой вопрос прямо в терминале, чтобы убедиться, что модель отвечает.*

5. **Как запустить тесты:**
   ```bash
   docker compose exec api pytest
   ```

## Доступные сервисы после запуска
- **Frontend (UI)**: `http://localhost:5173`
- **Backend (API)**: `http://localhost:8000` (Документация Swagger: `http://localhost:8000/docs`)

## Services
- **api**: FastAPI backend serving HTTP and SSE endpoints.
- **worker**: Celery worker for handling LLM inferences asynchronously.
- **db**: PostgreSQL database.
- **redis**: Used as a Celery broker and for Pub/Sub SSE streaming.
- **ollama**: Local LLM provider.
- **frontend**: React + TypeScript + Vite frontend.

## Code Quality & Linters
The project uses `pre-commit` to enforce code quality across both the backend (Python) and frontend (TypeScript/React).
To set up the pre-commit hooks locally:

1. Ensure you have `pre-commit` installed (`pip install pre-commit`).
2. Run `pre-commit install` in the root directory.

To run the linters manually on all files:
```bash
pre-commit run --all-files
```
