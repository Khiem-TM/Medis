from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.prescription import Prescription
    from app.models.user import User


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    diagnosis_name: Mapped[str] = mapped_column(String(200), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    facility: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    doctor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    symptoms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prescription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("prescriptions.id"), nullable=True, index=True
    )
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
    user: Mapped["User"] = relationship(back_populates="health_profiles")
    prescription: Mapped[Optional["Prescription"]] = relationship(
        foreign_keys=[prescription_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<HealthProfile id={self.id} user_id={self.user_id} diagnosis={self.diagnosis_name!r}>"
