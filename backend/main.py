from fastapi import FastAPI
from api import auth, conversations, admin
app = FastAPI(title="AI ChatBot API")

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Chatbot API пашет, а ты нет."}