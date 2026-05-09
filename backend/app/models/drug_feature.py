from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.drug import Drug


class DrugFeature(Base):
    __tablename__ = "drug_features"

    drug_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("drugs.id", ondelete="CASCADE"), primary_key=True
    )
    targets: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enzymes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pathways: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    smiles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    drug: Mapped["Drug"] = relationship(back_populates="features")
