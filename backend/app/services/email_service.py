# Email service — gửi transactional email qua SMTP (Gmail)
# Dùng fastapi-mail + Jinja2 templates
# Mọi lỗi gửi mail đều được log nhưng KHÔNG raise — tránh break auth flow

import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi import BackgroundTasks
from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"


class EmailService:
    def __init__(self):
        config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        self.mail = FastMail(config)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True,
        )

    # ------------------------------------------------------------------ #
    #  Public methods                                                      #
    # ------------------------------------------------------------------ #

    async def send_verification_email(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        full_name: str,
        token: str,
    ) -> None:
        """Gửi email xác thực tài khoản sau khi đăng ký (background task)."""
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        html = self._get_template(
            "verify_email.html",
            full_name=full_name,
            verify_link=verify_link,
            expire_hours=24,
        )
        message = MessageSchema(
            subject="[MediSmart] Xác thực địa chỉ email của bạn",
            recipients=[email],
            body=html,
            subtype=MessageType.html,
        )
        background_tasks.add_task(self._send, message)

    async def send_reset_password_email(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        full_name: str,
        token: str,
    ) -> None:
        """Gửi email đặt lại mật khẩu (background task)."""
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        html = self._get_template(
            "reset_password.html",
            full_name=full_name,
            reset_link=reset_link,
            expire_minutes=60,
        )
        message = MessageSchema(
            subject="[MediSmart] Yêu cầu đặt lại mật khẩu",
            recipients=[email],
            body=html,
            subtype=MessageType.html,
        )
        background_tasks.add_task(self._send, message)

    async def send_password_changed_notification(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        full_name: str,
        changed_at: str,
    ) -> None:
        """Gửi thông báo bảo mật khi mật khẩu vừa được thay đổi (background task)."""
        html = self._get_template(
            "password_changed.html",
            full_name=full_name,
            changed_at=changed_at,
            support_email="support@medismart.vn",
        )
        message = MessageSchema(
            subject="[MediSmart] Mật khẩu của bạn vừa được thay đổi",
            recipients=[email],
            body=html,
            subtype=MessageType.html,
        )
        background_tasks.add_task(self._send, message)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _get_template(self, template_name: str, **kwargs) -> str:
        """Load và render Jinja2 template, trả về HTML string."""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**kwargs)
        except TemplateNotFound:
            logger.error(f"Email template not found: {template_name}")
            return ""

    async def _send(self, message: MessageSchema) -> None:
        """Gửi email — bắt mọi exception để không break caller."""
        try:
            await self.mail.send_message(message)
        except Exception as exc:
            logger.error(f"Failed to send email to {message.recipients}: {exc}")
