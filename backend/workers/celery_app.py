import os
from celery import Celery

# Достаем адрес Redis из переменных окружения (помнишь, мы добавили REDIS_URL в docker-compose?)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Создаем само приложение Celery
# broker - это то, ГДЕ мы храним стикеры с задачами (наша очередь)
# backend - это то, ГДЕ мы храним результаты выполнения задач
celery_app = Celery(
    "chatbot_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Говорим Celery: "Ищи файлы с задачами в модуле worker.tasks"
celery_app.autodiscover_tasks(["workers.tasks"])