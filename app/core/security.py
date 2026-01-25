from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

from app.core.config import JWT_SECRET, JWT_EXPIRE_MINUTES

pwd_context = CryptoContext(Schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(password:str, hashed:str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(user_id:int):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")