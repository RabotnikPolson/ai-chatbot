import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Специальный форматер, который берет стандартный лог Питона
    и превращает его в красивую JSON-строку.
    """
    def format(self, record):
        # Базовые поля, которые есть в любом логе
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Если мы передали дополнительные поля (наши request_id, user_id и т.д.)
        # мы "приклеиваем" их к базовому словарю
        if hasattr(record, "custom_fields"):
            log_record.update(record.custom_fields)

        # Превращаем словарь в строку JSON (ensure_ascii=False чтобы русский текст не ломался)
        return json.dumps(log_record, ensure_ascii=False)

def setup_json_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False # Отключаем дублирование логов

    # Настраиваем логгер только если у него еще нет обработчиков (handlers)
    if not logger.handlers:
        handler = logging.StreamHandler() # Вывод в консоль
        handler.setFormatter(JSONFormatter()) # Подключаем наш JSON-форматер
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger