from fastapi import FastAPI
from api import auth

app = FastAPI(title="AI ChatBot API")


app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Chatbot API is running"}