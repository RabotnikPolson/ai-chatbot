# AI-Chatbot Project

This is the backend and soon-to-be frontend for the AI Chatbot application.

## Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)

## How to Run

1. Clone the repository.
2. Build and start the services using Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
3. The API will be available at `http://localhost:8000`.
4. The Redis and PostgreSQL databases will be spun up automatically.
5. The Ollama container will run locally for the LLM inference. Ensure you have the model pulled: `docker exec -it chatbot_ollama ollama run qwen2.5:0.5b`

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
