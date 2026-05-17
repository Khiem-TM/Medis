from __future__ import annotations

import enum
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.reminder import MedicationReminder
    from app.models.prescription import PrescriptionItem


class IntakeStatus(str, enum.Enum):
    pending = "pending"
    taken = "taken"
    late = "late"
    missed = "missed"


class MedicationIntakeLog(Base):
    __tablename__ = "medication_intake_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reminder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("medication_reminders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prescription_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("prescription_items.id", ondelete="SET NULL"), nullable=True
    )
    drug_name: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[IntakeStatus] = mapped_column(
        SAEnum(IntakeStatus), default=IntakeStatus.pending, nullable=False
    )
    taken_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="intake_logs")
    reminder: Mapped[Optional["MedicationReminder"]] = relationship()
    prescription_item: Mapped[Optional["PrescriptionItem"]] = relationship()

    def __repr__(self) -> str:
        return f"<MedicationIntakeLog id={self.id} reminder_id={self.reminder_id} status={self.status}>"
