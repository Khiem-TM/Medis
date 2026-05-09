import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, Boolean, Text, DateTime, ForeignKey, Enum as SAEnum, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class NotificationType(str, enum.Enum):
    medication_reminder = "medication_reminder"
    health_alert = "health_alert"
    system = "system"
    daily_summary = "daily_summary"

class NotificationPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType), nullable=False)
    priority: Mapped[NotificationPriority] = mapped_column(
        SAEnum(NotificationPriority), default=NotificationPriority.medium, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for extra data
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("medication_reminders.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")
