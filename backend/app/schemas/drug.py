from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.drug import InteractionSeverity


# ── Drug ───────────────────────────────────────────────────────────────────

class DrugProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id: str
    trade_name: str
    route: str
    dosage: str
    formulation: str
    origin: str


class DrugWarningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id: str
    warning_text: str


class DrugInteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id_1: str
    drug_id_2: str
    interaction_type: Optional[str] = None
    severity: InteractionSeverity
    description: Optional[str] = None
    recommendation: Optional[str] = None
    # Populated by service layer (not on ORM model directly)
    drug_1_name: Optional[str] = None
    drug_2_name: Optional[str] = None


class DrugListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    atc_code: Optional[str] = None
    dosage_form: Optional[str] = None


class DrugDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    atc_code: Optional[str] = None
    dosage_form: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = None
    products: List[DrugProductResponse] = []
    warnings: List[DrugWarningResponse] = []
    created_at: datetime


# ── Interaction check ──────────────────────────────────────────────────────

class InteractionCheckRequest(BaseModel):
    drug_ids: List[str]

    @field_validator("drug_ids")
    @classmethod
    def validate_drug_ids(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("Cần ít nhất 2 thuốc để kiểm tra tương tác")
        if len(v) > 20:
            raise ValueError("Tối đa 20 thuốc mỗi lần kiểm tra")
        if len(v) != len(set(v)):
            raise ValueError("Danh sách thuốc không được có trùng lặp")
        return v


class SafePairInfo(BaseModel):
    drug_id_1: str
    drug_id_2: str
    drug_1_name: Optional[str] = None
    drug_2_name: Optional[str] = None


class InteractionCheckResult(BaseModel):
    checked_drugs: List[str]
    total_pairs: int
    has_interaction: bool
    interactions: List[DrugInteractionResponse]
    safe_pairs: List[SafePairInfo]
