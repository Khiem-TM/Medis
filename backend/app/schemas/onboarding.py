import json
from typing import Optional, List
from pydantic import BaseModel, field_validator

class AllergyItem(BaseModel):
    drug: str
    reaction: Optional[str] = None

class MedicationItem(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None

class OnboardingStep1Request(BaseModel):
    """Basic health info"""
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_type: Optional[str] = None
    is_pregnant: bool = False
    is_breastfeeding: bool = False
    kidney_function: str = "normal"
    liver_function: str = "normal"

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        if v.upper() not in valid:
            raise ValueError("Nhóm máu không hợp lệ")
        return v.upper()

    @field_validator("height_cm")
    @classmethod
    def validate_height(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (50 <= v <= 250):
            raise ValueError("Chiều cao phải từ 50-250 cm")
        return v

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (10 <= v <= 500):
            raise ValueError("Cân nặng phải từ 10-500 kg")
        return v

class OnboardingStep2Request(BaseModel):
    """Conditions & allergies - accepts free text or structured"""
    conditions_text: Optional[str] = None  # Vietnamese free text
    allergies_text: Optional[str] = None   # Vietnamese free text
    conditions: Optional[List[str]] = None  # Structured list
    allergies: Optional[List[AllergyItem]] = None  # Structured list

class OnboardingStep3Request(BaseModel):
    """Current medications & goals"""
    medications_text: Optional[str] = None  # Free text
    medications: Optional[List[MedicationItem]] = None
    health_goals: Optional[List[str]] = None

class OnboardingStatusResponse(BaseModel):
    model_config = {"from_attributes": True}
    onboarding_completed: bool
    onboarding_step: int

class HealthBaselineResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    user_id: int
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_type: Optional[str] = None
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    is_pregnant: bool
    is_breastfeeding: bool
    kidney_function: str
    liver_function: str
    health_goals: Optional[str] = None
    onboarding_completed: bool
    onboarding_step: int

class ParsedConditionsResponse(BaseModel):
    conditions: List[str] = []
    allergies: List[AllergyItem] = []
    medications: List[MedicationItem] = []
    raw_text: str
