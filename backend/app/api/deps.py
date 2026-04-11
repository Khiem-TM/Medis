from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from sqlalchemy import select
from app.database import get_db
from app.redis_client import get_redis
from app.core.security import decode_token
from app.models.user import User, UserRole

# HTTPBearer tự động parse "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Kiểm tra blacklist Redis
    jti = payload.get("jti")
    if jti and await redis.exists(f"blacklist:{jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã bị thu hồi. Vui lòng đăng nhập lại.",
        )
    
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa",
        )

    return user

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User | None:
    """Return the authenticated user if a valid Bearer token is provided, else None."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    jti = payload.get("jti")
    if jti and await redis.exists(f"blacklist:{jti}"):
        return None
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này",
        )
    return current_user

# File trên này xử Authen/Author để inject user/admin vào các route cần thiết.
# Nó tương đương với guard trong NestJS.