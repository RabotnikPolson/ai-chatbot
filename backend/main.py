import os
import redis
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi.middleware.cors import CORSMiddleware

from api import auth, conversations, admin
from api.auth import get_db

app = FastAPI(title="AI ChatBot API")

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(conversations.messages_router)
app.include_router(admin.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Chatbot API пашет, а ты нет."}


@app.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)):
    status = {
        "db": "ok",
        "redis": "ok"
    }

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        status["db"] = f"error: {str(e)}"

    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
    except Exception as e:
        status["redis"] = f"error: {str(e)}"


    if status["db"] != "ok" or status["redis"] != "ok":
        raise HTTPException(status_code=503, detail=status)

    return {"status": "all systems go", "details": status}