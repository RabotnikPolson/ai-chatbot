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
- **frontend**: Next.js application (Work In Progress).
