from passlib.context import CryptContext
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from datetime import datetime, timedelta

from app.core.config import JWT_SECRET, JWT_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def decode_access_token(token: str) -> int:
    """Decode JWT token and return user_id"""
    try:
        # Decode without validation first to check format
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_signature": True})
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing user_id")
        # Handle both string and integer sub (for backwards compatibility)
        return int(user_id)
    except ExpiredSignatureError:
        raise ValueError("Token has expired - please login again")
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid user_id in token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Token decode error: {str(e)}")

def hash_password(password: str) -> str:
    """Hash password using bcrypt. Password must be <= 72 bytes."""
    # Safety check: bcrypt has a 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError('Password cannot exceed 72 bytes')
    return pwd_context.hash(password)

def verify_password(password:str, hashed:str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(user_id: int) -> str:
    """Create JWT access token for user"""
    payload = {
        "sub": str(user_id),  # JWT standard uses string for 'sub'
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iat": datetime.utcnow()  # issued at
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")