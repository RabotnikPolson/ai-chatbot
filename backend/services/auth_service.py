from sqlalchemy.orm import Session
from fastapi import HTTPException
import jwt
from db.models import User
from schemas.user import UserCreate
from services.security import get_password_hash, verify_password, create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email is already in use")

        hashed_pwd = get_password_hash(user_data.password)
        new_user = User(email=user_data.email, password_hash=hashed_pwd)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        return user

    @staticmethod
    def create_tokens_for_user(user_id: int):
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return {"access_token": access_token, "refresh_token": refresh_token}

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Token is invalid or expired")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token}

