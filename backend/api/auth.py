from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from schemas.user import UserCreate, UserResponse, Token, RefreshTokenRequest
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    return AuthService.register_user(db, user_data)

@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    tokens = AuthService.create_tokens_for_user(user.id)
    tokens["token_type"] = "bearer"
    return tokens

@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    tokens = AuthService.refresh_access_token(db, request.refresh_token)
    tokens["token_type"] = "bearer"
    return tokens

@router.get("/me")
def get_my_profile(token: str = Depends(oauth2_scheme)):
    return {
        "message": "VALAR MARGULIS!",
        "your_token": token
    }