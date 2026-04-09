from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # Hash password using bcrypt
    return pwd_context.hash(password)

# So sanh
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int, role: str) -> tuple[str, str]:
    jlt = str(uuid.uuid4())  # Unique JWT ID
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "jlt": jlt,  # Unique JWT ID để có thể blacklist nếu cần
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jlt


def create_refresh_token(user_id: int) -> tuple[str, str]:
    jlt = str(uuid.uuid4())  # Unique JWT ID
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jlt": jlt,  # Unique JWT ID để có thể blacklist nếu cần
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jlt

def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
    
