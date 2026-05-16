from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.onboarding import AllergyItem, MedicationItem
from app.schemas.user import HealthProfileListItem


class HealthBaselineStructured(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_type: Optional[str] = None
    chronic_conditions: list[str] = []
    allergies: list[AllergyItem] = []
    current_medications: list[MedicationItem] = []
    is_pregnant: bool
    is_breastfeeding: bool
    kidney_function: str
    liver_function: str
    health_goals: list[str] = []
    onboarding_completed: bool
    onboarding_step: int
    created_at: datetime
    updated_at: datetime


class HealthBaselineUpdate(BaseModel):
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_type: Optional[str] = None
    chronic_conditions: Optional[list[str]] = None
    allergies: Optional[list[AllergyItem]] = None
    current_medications: Optional[list[MedicationItem]] = None
    is_pregnant: Optional[bool] = None
    is_breastfeeding: Optional[bool] = None
    kidney_function: Optional[str] = None
    liver_function: Optional[str] = None
    health_goals: Optional[list[str]] = None

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        normalized = value.upper()
        valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        if normalized not in valid:
            raise ValueError("Nhóm máu không hợp lệ")
        return normalized

    @field_validator("height_cm")
    @classmethod
    def validate_height(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not (50 <= value <= 250):
            raise ValueError("Chiều cao phải từ 50-250 cm")
        return value

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not (10 <= value <= 500):
            raise ValueError("Cân nặng phải từ 10-500 kg")
        return value


class HealthSummaryResponse(BaseModel):
    baseline: HealthBaselineStructured
    recent_visits: list[HealthProfileListItem]
    total_visits: int
    active_prescriptions: int
    active_reminders: int
    last_exam_date: Optional[date] = None
