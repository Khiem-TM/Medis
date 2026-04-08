from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis
from fastapi import HTTPException, status
from app.models.user import User, AuthProvider
from app.schemas.auth import (
    RegisterRequest, LoginRequest,
    RefreshRequest, ResetPasswordRequest
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token
)
from app.config import settings
import hashlib
import time

class AuthService: 
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    # register
    async def register(self, req: RegisterRequest) -> User:
        result = await self.db.execute(select(User).where(User.email == req.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã tồn tại")
        
        result = await self.db.execute(select(User).where(User.username == req.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã tồn tại")
        
        user = User(
            username=req.username,
            email=req.email,
            password_hash=hash_password(req.password),
            full_name=req.full_name,
            phone=req.phone,
            auth_provider=AuthProvider.local,
        )

        self.db.add(user)
        await self.db.flush()  # Để có ID của user mới tạo
        return user
    
    # login
    async def login(self, req: LoginRequest) -> dict:
        result = await self.db.execute(
            select(User).where(
                User.username == req.username
            )
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai username hoặc password")
        
        # Kiểm tra password
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai username hoặc password")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa")
        
        return await self._create_tokens_pair(user)
    

    # logout
    async def logout(self, access_token: str, user_id:int) -> None:
        payload = decode_token(access_token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            remaining_ttl = int(exp - time.time())

            if remaining_ttl > 0 and jti:
                # Blacklist JWT ID trong Redis với TTL bằng thời gian còn lại của token
                await self.redis.setex(f"blacklist:{jti}", remaining_ttl, "true")

        # delete refresh token
        await self.redis.delete(f"refresh_token:{user_id}")

    # refresh token
    async def refresh_token(self, req: RefreshRequest) -> dict:
        payload = decode_token(req.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="Refresh token không hợp lệ")
        
        user_id = int(payload["sub"])
        jti = payload["jti"]

        # Verify refresh token hash trong Redis
        stored_hash = await self.redis.get(f"refresh:{user_id}")
        token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()

        if not stored_hash or stored_hash != token_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token đã hết hạn hoặc không hợp lệ"
            )
        
        # Lấy user từ DB
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản không tồn tại"
            )

        # Tạo token mới (rotate refresh token)
        return await self._create_token_pair(user)

    # helpers --> create token pair and save to Redis
    async def _create_token_pair(self, user: User) -> dict:
        access_token, access_jti = create_access_token(user.id, user.role)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        # Lưu refresh token hash vào Redis
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.redis.setex(
            f"refresh:{user.id}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,  # Convert ngày → giây
            token_hash
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
