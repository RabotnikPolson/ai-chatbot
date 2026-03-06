from fastapi import APIRouter, Depends, Response, Cookie, HTTPException, status
from sqlalchemy.orm import Session
from db.database import SessionLocal
from schemas.user import UserCreate, UserResponse, Token
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

@router.post("/login")
def login_user(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    tokens = AuthService.create_tokens_for_user(user.id)
    
    # Set the refresh token as an httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in production (HTTPS)
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(response: Response, refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
        
    tokens = AuthService.refresh_access_token(db, refresh_token)
    
    # Update the refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 24 * 60 * 60
    )
    
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer"
    }

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_my_profile(token: str = Depends(oauth2_scheme)):
    return {
        "message": "VALAR MARGULIS!",
        "your_token": token
    }