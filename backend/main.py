from fastapi import FastAPI
from api import auth, conversations

app = FastAPI(title="AI ChatBot API")

app.include_router(auth.router)
app.include_router(conversations.router)

@app.get("/")
def read_root():
    return {"message": "Chatbot API пашет, а ты нет."}