from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class VitalRecord(Base):
    __tablename__ = "vital_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)       # bpm
    systolic_bp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # mmHg
    diastolic_bp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)     # mmHg
    blood_glucose: Mapped[Optional[float]] = mapped_column(Float, nullable=True)    # mmol/L
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<VitalRecord id={self.id} user_id={self.user_id} at={self.recorded_at}>"
