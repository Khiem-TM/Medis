import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, Boolean, Float, Text, DateTime, ForeignKey, Enum as SAEnum, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class KidneyFunction(str, enum.Enum):
    normal = "normal"
    mild_impairment = "mild_impairment"
    moderate_impairment = "moderate_impairment"
    severe_impairment = "severe_impairment"

class LiverFunction(str, enum.Enum):
    normal = "normal"
    mild_impairment = "mild_impairment"
    moderate_impairment = "moderate_impairment"
    severe_impairment = "severe_impairment"

class UserHealthBaseline(Base):
    __tablename__ = "user_health_baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    blood_type: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    chronic_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    current_medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    is_pregnant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_breastfeeding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kidney_function: Mapped[KidneyFunction] = mapped_column(
        SAEnum(KidneyFunction), default=KidneyFunction.normal, nullable=False
    )
    liver_function: Mapped[LiverFunction] = mapped_column(
        SAEnum(LiverFunction), default=LiverFunction.normal, nullable=False
    )
    health_goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="health_baseline")
