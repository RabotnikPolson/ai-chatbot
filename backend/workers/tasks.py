import time
from workers.celery_app import celery_app
from db.database import SessionLocal
from db.models import Message, MessageStatusEnum

# Декоратор @celery_app.task превращает обычную функцию в фоновую задачу Celery
@celery_app.task(name="generate_reply")
def generate_reply(message_id: int):
    # Воркер работает в отдельном процессе, поэтому ему нужна своя сессия для работы с БД!
    db = SessionLocal()
    try:
        # Достаем то самое пустое сообщение со статусом "queued"
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            return "Message not found" # Если не нашли, просто выходим

        # 1. Меняем статус на "в процессе"
        msg.status = MessageStatusEnum.processing
        db.commit()

        # 2. Имитируем тяжелую работу нейросети (спим 5 секунд)
        time.sleep(5)

        # 3. Пишем ответ и ставим финальный статус
        msg.content = "Привет! Я сгенерирован настоящим Celery-воркером через Redis!"
        msg.status = MessageStatusEnum.done
        db.commit()

        return "Success"
    except Exception as e:
        # Если что-то упало (например, отвалилась БД), ставим статус failed
        db.rollback()
        if msg:
            msg.status = MessageStatusEnum.failed
            msg.error = str(e)
            db.commit()
        raise e
    finally:
        # ОБЯЗАТЕЛЬНО закрываем сессию БД
        db.close()