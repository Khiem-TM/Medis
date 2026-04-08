import logging
import re
import secrets
from typing import Any

import httpx
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from fastapi import HTTPException, status

from app.config import settings
from app.models.user import User, AuthProvider, UserRole

logger = logging.getLogger(__name__)

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
STATE_TTL = 600  # 10 phút


def _build_flow() -> Flow:
    """Tạo Flow instance từ config (stateless, gọi mỗi request)."""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


class GoogleOAuthService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis


    async def get_authorization_url(self) -> tuple[str, str]:
        """Tạo Google OAuth URL và lưu state vào Redis để chống CSRF.

        Returns: (authorization_url, state)
        """
        state = secrets.token_urlsafe(32)
        await self.redis.setex(f"oauth:state:{state}", STATE_TTL, "1")

        flow = _build_flow()
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="select_account",
        )
        logger.info("Generated Google OAuth authorization URL")
        return authorization_url, state


    async def verify_state(self, state: str) -> bool:
        """Kiểm tra state có hợp lệ không (one-time use).

        Returns: True nếu hợp lệ, False nếu không tồn tại/đã dùng.
        """
        key = f"oauth:state:{state}"
        exists = await self.redis.exists(key)
        if exists:
            await self.redis.delete(key)
            return True
        return False

    async def get_user_info(self, code: str) -> dict[str, Any]:
        """Đổi authorization code lấy access token, rồi gọi Google UserInfo API.

        Returns: dict với google_id, email, name, picture
        Raises:  HTTPException 400 nếu Google từ chối hoặc thiếu field bắt buộc.
        """
        flow = _build_flow()
        try:
            flow.fetch_token(code=code)
        except Exception as exc:
            logger.error(f"Failed to exchange Google OAuth code: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xác thực với Google. Vui lòng thử lại.",
            )

        access_token = flow.credentials.token
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Google UserInfo API error: {exc.response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể lấy thông tin từ Google.",
            )
        except Exception as exc:
            logger.error(f"Unexpected error calling Google UserInfo API: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lỗi kết nối tới Google.",
            )

        google_id = data.get("id")
        email = data.get("email")
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google không trả về đủ thông tin cần thiết.",
            )

        return {
            "google_id": google_id,
            "email": email,
            "name": data.get("name", ""),
            "picture": data.get("picture", ""),
        }


    async def find_or_create_user(self, google_info: dict[str, Any]) -> User:
        """Xử lý 3 cases: user đã có Google, user local, user mới hoàn toàn.

        Returns: User (đã flush, chưa commit — get_db sẽ commit sau)
        """
        google_id: str = google_info["google_id"]
        email: str = google_info["email"]
        name: str = google_info["name"]
        picture: str = google_info["picture"]

        # Case A — Đã có account Google
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()
        if user:
            if picture and user.avatar_url != picture:
                user.avatar_url = picture
                logger.info(f"Updated avatar for Google user {user.id}")
            return user

        # Case B — Có account local cùng email → link Google
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user:
            user.google_id = google_id
            user.auth_provider = AuthProvider.google
            if picture and not user.avatar_url:
                user.avatar_url = picture
            logger.info(f"Linked Google account to existing local user {user.id}")
            return user

        # Case C — Tạo user mới
        base_username = re.sub(r"[^a-zA-Z0-9_]", "", email.split("@")[0]) or "user"
        username = await self._generate_unique_username(base_username)

        user = User(
            username=username,
            email=email,
            full_name=name,
            google_id=google_id,
            avatar_url=picture or None,
            auth_provider=AuthProvider.google,
            role=UserRole.user,
            is_active=True,  # Google đã verify email
            password_hash=None,
        )
        self.db.add(user)
        await self.db.flush()
        logger.info(f"Created new user via Google OAuth: {user.email}")
        return user

    async def _generate_unique_username(self, base: str) -> str:
        """Thử base username, nếu trùng thêm 4 số random, tối đa 10 lần."""
        candidate = base[:30]  # Giới hạn max length của username column
        for attempt in range(10):
            result = await self.db.execute(
                select(User).where(User.username == candidate)
            )
            if not result.scalar_one_or_none():
                return candidate
            suffix = secrets.randbelow(9000) + 1000  # 1000–9999
            candidate = f"{base[:25]}_{suffix}"
            logger.debug(f"Username '{base}' taken, trying '{candidate}' (attempt {attempt + 1})")

        # Fallback: uuid suffix không bao giờ trùng
        return f"{base[:20]}_{secrets.token_hex(4)}"
