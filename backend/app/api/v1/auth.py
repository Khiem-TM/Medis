from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db
from app.redis_client import get_redis
from app.api.deps import get_current_user, bearer_scheme
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshTokenRequest, ForgotPasswordRequest,
    ResetPasswordRequest, ResendVerificationRequest,
    OtpForgotPasswordRequest, VerifyResetOtpRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.oauth_service import GoogleOAuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_service(db: AsyncSession, redis: Redis) -> AuthService:
    return AuthService(db, redis, EmailService())


# ------------------------------------------------------------------ #
#  Register / Verify                                                  #
# ------------------------------------------------------------------ #

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.register(req, background_tasks)
    await db.commit()
    return {"message": "Đăng ký thành công. Vui lòng kiểm tra email để xác thực tài khoản."}


@router.get("/verify-email", summary="Xác thực email qua token")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.verify_email(token)
    await db.commit()
    return {"message": "Xác thực email thành công. Bạn có thể đăng nhập ngay bây giờ."}


@router.post("/resend-verification", summary="Gửi lại email xác thực")
async def resend_verification(
    req: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.resend_verification(req.email, background_tasks)
    return {"message": "Nếu email tồn tại và chưa xác thực, hướng dẫn đã được gửi."}


# ------------------------------------------------------------------ #
#  Login / Logout / Refresh                                           #
# ------------------------------------------------------------------ #

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    token_data = await service.login(req)
    return token_data


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.logout(credentials.credentials, current_user.id)
    return {"message": "Đăng xuất thành công"}


@router.post("/refresh", response_model=TokenResponse, summary="Làm mới Access Token")
async def refresh_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    return await service.refresh_token(req)


# ------------------------------------------------------------------ #
#  Password management                                                #
# ------------------------------------------------------------------ #

@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.forgot_password(req.email, background_tasks)
    return {"message": "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi."}


@router.post("/forgot-password/otp", summary="Gửi mã OTP đặt lại mật khẩu")
async def forgot_password_otp(
    req: OtpForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.forgot_password_otp(req.email, background_tasks)
    return {"message": "Nếu email tồn tại, mã OTP đã được gửi đến email của bạn."}


@router.post("/verify-reset-otp", summary="Xác thực OTP và nhận reset token")
async def verify_reset_otp(
    req: VerifyResetOtpRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    reset_token = await service.verify_reset_otp(req.email, req.otp)
    return {"reset_token": reset_token}


@router.post("/reset-password", summary="Đặt lại mật khẩu bằng token")
async def reset_password(
    req: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = _auth_service(db, redis)
    await service.reset_password(req.token, req.new_password, background_tasks)
    await db.commit()
    return {"message": "Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập lại."}


# ------------------------------------------------------------------ #
#  Profile                                                            #
# ------------------------------------------------------------------ #

@router.get("/me", response_model=UserResponse, summary="Lấy thông tin user hiện tại")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ------------------------------------------------------------------ #
#  Google OAuth                                                       #
# ------------------------------------------------------------------ #

@router.get("/google/login", summary="Redirect sang Google để đăng nhập")
async def google_login(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    oauth_service = GoogleOAuthService(db, redis)
    authorization_url, _ = await oauth_service.get_authorization_url()
    return RedirectResponse(url=authorization_url)


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    description="Google redirect về đây sau khi user đồng ý. Tạo token và redirect về frontend.",
    include_in_schema=False,  # Không hiển thị trên Swagger (không thể test trực tiếp)
)
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    from app.config import settings as app_settings

    oauth_service = GoogleOAuthService(db, redis)

    if not await oauth_service.verify_state(state):
        return RedirectResponse(url=f"{app_settings.FRONTEND_URL}/login?error=invalid_state")

    try:
        google_info = await oauth_service.get_user_info(code)
        user = await oauth_service.find_or_create_user(google_info)
        auth_svc = _auth_service(db, redis)
        token_data = await auth_svc._create_token_pair(user)
    except HTTPException:
        return RedirectResponse(url=f"{app_settings.FRONTEND_URL}/login?error=oauth_failed")
    except Exception:
        return RedirectResponse(url=f"{app_settings.FRONTEND_URL}/login?error=oauth_failed")

    return RedirectResponse(
        url=(
            f"{app_settings.FRONTEND_URL}/auth/callback"
            f"?access_token={token_data['access_token']}"
            f"&refresh_token={token_data['refresh_token']}"
        )
    )
