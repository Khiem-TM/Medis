from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.prescription import PrescriptionItem


class MedicationReminder(Base):
    __tablename__ = "medication_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prescription_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("prescription_items.id", ondelete="SET NULL"), nullable=True
    )
    drug_name: Mapped[str] = mapped_column(String(200), nullable=False)
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    # Comma-separated days: "mon,tue,wed,thu,fri,sat,sun" or "daily"
    frequency: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)
    days_of_week: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="reminders")
    prescription_item: Mapped[Optional["PrescriptionItem"]] = relationship()

    def __repr__(self) -> str:
        return f"<MedicationReminder id={self.id} drug_name={self.drug_name!r} time={self.reminder_time}>"
