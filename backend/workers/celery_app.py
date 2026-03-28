import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "chatbot_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.autodiscover_tasks(["workers.tasks"])