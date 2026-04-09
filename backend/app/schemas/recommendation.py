from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, field_validator


class RecommendationRequest(BaseModel):
    symptoms: str
    health_profile_ids: Optional[List[int]] = None
    current_prescription_id: Optional[int] = None

    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Mô tả triệu chứng cần ít nhất 10 ký tự")
        if len(v) > 1000:
            raise ValueError("Mô tả triệu chứng không vượt quá 1000 ký tự")
        return v

    @field_validator("health_profile_ids")
    @classmethod
    def validate_profile_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None and len(v) > 5:
            raise ValueError("Tối đa 5 hồ sơ bệnh án mỗi lần")
        return v


class DrugSuggestion(BaseModel):
    drug_name: str
    active_ingredient: str
    indication: str
    reference_dosage: str
    suitability_score: int
    warnings: Optional[str] = None
    drug_id: Optional[str] = None
    has_interaction: bool = False


class RecommendationResponse(BaseModel):
    model_config = {"from_attributes": False}

    request_id: str
    symptoms: str
    suggestions: List[DrugSuggestion]
    general_advice: str
    see_doctor_if: str
    generated_at: datetime
