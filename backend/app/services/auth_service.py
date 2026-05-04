import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import AuthProvider, User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

# Redis TTLs
_VERIFY_EMAIL_TTL = 24 * 3600   # 24 giờ
_RESET_PASSWORD_TTL = 3600       # 1 giờ
_RATE_LIMIT_TTL = 300            # 5 phút
_OTP_RESET_TTL = 600             # 10 phút cho OTP
_OTP_RESET_TOKEN_TTL = 900       # 15 phút cho short-lived reset token sau OTP


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis, email_service: EmailService | None = None):
        self.db = db
        self.redis = redis
        self.email_service = email_service


    async def register(self, req: RegisterRequest, background_tasks: BackgroundTasks) -> User:
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
            is_active=False,  # Phải xác thực email trước
        )
        self.db.add(user)
        await self.db.flush()  # Lấy user.id

        # Tạo và lưu verify token
        verify_token = str(uuid.uuid4())
        await self.redis.setex(f"verify:email:{verify_token}", _VERIFY_EMAIL_TTL, str(user.id))
        await self.redis.setex(f"verify:user:{user.id}", _VERIFY_EMAIL_TTL, verify_token)

        if self.email_service:
            await self.email_service.send_verification_email(
                background_tasks, req.email, req.full_name, verify_token
            )
        logger.info(f"New user registered (pending verification): {user.email}")
        return user

    async def login(self, req: LoginRequest) -> dict:
        result = await self.db.execute(select(User).where(User.username == req.username))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sai username hoặc password",
            )

        if not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sai username hoặc password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản chưa được kích hoạt. Vui lòng kiểm tra email để xác thực.",
            )

        return await self._create_token_pair(user)


    async def verify_email(self, token: str) -> User:
        user_id_raw = await self.redis.get(f"verify:email:{token}")
        if not user_id_raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link xác thực không hợp lệ hoặc đã hết hạn",
            )

        user_id = int(user_id_raw)
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản không tồn tại",
            )
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản đã được xác thực",
            )

        user.is_active = True
        await self.redis.delete(f"verify:email:{token}")
        await self.redis.delete(f"verify:user:{user_id}")
        logger.info(f"Email verified for user {user_id}")
        return user


    async def resend_verification(self, email: str, background_tasks: BackgroundTasks) -> None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or user.is_active:
            return  # Không tiết lộ email tồn tại hay không

        # Rate limit: 1 lần / 5 phút
        if await self.redis.exists(f"resend:limit:{user.id}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vui lòng chờ 5 phút trước khi gửi lại email xác thực",
            )

        # Xóa token cũ nếu có (dùng reverse mapping để tránh SCAN)
        old_token_raw = await self.redis.get(f"verify:user:{user.id}")
        if old_token_raw:
            old_token = old_token_raw
            await self.redis.delete(f"verify:email:{old_token}")
            await self.redis.delete(f"verify:user:{user.id}")

        # Tạo token mới
        verify_token = str(uuid.uuid4())
        await self.redis.setex(f"verify:email:{verify_token}", _VERIFY_EMAIL_TTL, str(user.id))
        await self.redis.setex(f"verify:user:{user.id}", _VERIFY_EMAIL_TTL, verify_token)
        await self.redis.setex(f"resend:limit:{user.id}", _RATE_LIMIT_TTL, "1")

        if self.email_service:
            await self.email_service.send_verification_email(
                background_tasks, user.email, user.full_name or "", verify_token
            )
        logger.info(f"Resent verification email to {email}")


    async def forgot_password(self, email: str, background_tasks: BackgroundTasks) -> None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        # Không báo lỗi dù email không tồn tại (tránh email enumeration)
        if not user or user.auth_provider == AuthProvider.google:
            return

        # Rate limit
        if await self.redis.exists(f"reset:limit:{user.id}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vui lòng chờ 5 phút trước khi gửi lại yêu cầu đặt lại mật khẩu",
            )

        reset_token = str(uuid.uuid4())
        await self.redis.setex(f"reset:password:{reset_token}", _RESET_PASSWORD_TTL, str(user.id))
        await self.redis.setex(f"reset:limit:{user.id}", _RATE_LIMIT_TTL, "1")

        if self.email_service:
            await self.email_service.send_reset_password_email(
                background_tasks, user.email, user.full_name or "", reset_token
            )
        logger.info(f"Password reset email sent to {email}")


    async def reset_password(
        self, token: str, new_password: str, background_tasks: BackgroundTasks
    ) -> None:
        user_id_raw = await self.redis.get(f"reset:password:{token}")
        if not user_id_raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn",
            )

        _validate_password(new_password)

        user_id = int(user_id_raw)
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản không tồn tại",
            )

        user.password_hash = hash_password(new_password)
        await self.redis.delete(f"reset:password:{token}")
        await self.redis.delete(f"refresh:{user_id}")  # Đăng xuất khỏi tất cả thiết bị

        changed_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        if self.email_service:
            await self.email_service.send_password_changed_notification(
                background_tasks, user.email, user.full_name or "", changed_at
            )
        logger.info(f"Password reset successfully for user {user_id}")


    async def forgot_password_otp(self, email: str, background_tasks: BackgroundTasks) -> None:
        """Gửi mã OTP 6 chữ số để đặt lại mật khẩu."""
        import random
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or user.auth_provider == AuthProvider.google:
            return  # Silent - không tiết lộ email

        # Rate limit: 1 OTP / 5 phút
        if await self.redis.exists(f"otp:reset:limit:{user.id}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vui lòng chờ 5 phút trước khi gửi lại mã OTP",
            )

        otp = str(random.randint(100000, 999999))
        await self.redis.setex(f"otp:reset:{email}", _OTP_RESET_TTL, otp)
        await self.redis.setex(f"otp:reset:limit:{user.id}", _RATE_LIMIT_TTL, "1")

        if self.email_service:
            await self.email_service.send_otp_email(
                background_tasks, email, user.full_name or "", otp
            )
        logger.info(f"OTP reset sent to {email}")

    async def verify_reset_otp(self, email: str, otp: str) -> str:
        """Xác thực OTP và trả về reset token ngắn hạn."""
        stored_otp = await self.redis.get(f"otp:reset:{email}")
        if not stored_otp or stored_otp != otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã OTP không đúng hoặc đã hết hạn",
            )

        await self.redis.delete(f"otp:reset:{email}")

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản không tồn tại",
            )

        # Issue short-lived reset token (reuse existing reset:password: key pattern)
        reset_token = str(uuid.uuid4())
        await self.redis.setex(f"reset:password:{reset_token}", _OTP_RESET_TOKEN_TTL, str(user.id))
        logger.info(f"OTP verified, reset token issued for user {user.id}")
        return reset_token

    async def logout(self, access_token: str, user_id: int) -> None:
        payload = decode_token(access_token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            remaining_ttl = int(exp - time.time())
            if remaining_ttl > 0 and jti:
                await self.redis.setex(f"blacklist:{jti}", remaining_ttl, "true")

        await self.redis.delete(f"refresh:{user_id}")


    async def refresh_token(self, req: RefreshTokenRequest) -> dict:
        payload = decode_token(req.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token không hợp lệ",
            )

        user_id = int(payload["sub"])

        stored_hash = await self.redis.get(f"refresh:{user_id}")
        token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
        if not stored_hash or stored_hash != token_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token đã hết hạn hoặc không hợp lệ",
            )

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản không tồn tại",
            )

        return await self._create_token_pair(user)

    async def _create_token_pair(self, user: User) -> dict:
        access_token, _ = create_access_token(user.id, user.role)
        refresh_token, _ = create_refresh_token(user.id)

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.redis.setex(
            f"refresh:{user.id}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            token_hash,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


def _validate_password(password: str) -> None:
    """Kiểm tra độ mạnh password: min 14 ký tự, hoa/thường/số/đặc biệt."""
    errors = []
    if len(password) < 14:
        errors.append("Mật khẩu phải có ít nhất 14 ký tự")
    if not re.search(r"[A-Z]", password):
        errors.append("Phải có ít nhất 1 chữ hoa")
    if not re.search(r"[a-z]", password):
        errors.append("Phải có ít nhất 1 chữ thường")
    if not re.search(r"[0-9]", password):
        errors.append("Phải có ít nhất 1 chữ số")
    if not re.search(r"[@$!%*?&]", password):
        errors.append("Phải có ít nhất 1 ký tự đặc biệt (@$!%*?&)")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="; ".join(errors),
        )
