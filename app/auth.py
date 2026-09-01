from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from .models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGO = "HS256"

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)

def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, settings.jwt_secret, algorithm=ALGO)

def get_current_user(request: Request, db: Session) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401)
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401)
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401)
    return user
