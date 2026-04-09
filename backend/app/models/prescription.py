from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.drug import Drug
    from app.models.user import User


class PrescriptionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[PrescriptionStatus] = mapped_column(
        SAEnum(PrescriptionStatus),
        default=PrescriptionStatus.active,
        nullable=False,
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
    user: Mapped["User"] = relationship(back_populates="prescriptions")
    items: Mapped[List["PrescriptionItem"]] = relationship(
        back_populates="prescription",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Prescription id={self.id} user_id={self.user_id} name={self.name!r}>"


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(
        ForeignKey("prescriptions.id"), nullable=False, index=True
    )
    drug_id: Mapped[Optional[str]] = mapped_column(
        String(10),
        ForeignKey("drugs.id"),
        nullable=True,  # OCR có thể chưa map được drug_id
    )
    drug_name: Mapped[str] = mapped_column(String(200), nullable=False)  # Giữ tên dù drug bị xóa
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    prescription: Mapped["Prescription"] = relationship(back_populates="items")
    drug: Mapped[Optional["Drug"]] = relationship(
        foreign_keys=[drug_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PrescriptionItem id={self.id} drug_name={self.drug_name!r}>"
