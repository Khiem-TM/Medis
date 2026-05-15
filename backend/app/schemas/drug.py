from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ── Drug Warning ────────────────────────────────────────────────────────────

class DrugWarningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id: str
    warning_text: str


# ── Drug Event Type ─────────────────────────────────────────────────────────

class DrugEventTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_name: str
    description: Optional[str] = None
    source_event_id: Optional[int] = None


# ── Drug Feature ─────────────────────────────────────────────────────────────

class DrugFeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drug_id: str
    targets: Optional[str] = None
    enzymes: Optional[str] = None
    pathways: Optional[str] = None
    smiles: Optional[str] = None


# ── Drug Interaction ────────────────────────────────────────────────────────

class DrugInteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drug_id: str
    interacts_with_id: str
    interacts_with_name: Optional[str] = None
    # Populated by service layer
    drug_name: Optional[str] = None
    event_type_id: Optional[int] = None
    interaction_label: Optional[str] = None
    source: Optional[str] = None
    confidence_score: Optional[float] = None
    event_type: Optional[DrugEventTypeResponse] = None


# ── Drug List / Detail ──────────────────────────────────────────────────────

class DrugListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    generic_name: str


class DrugDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    generic_name: str
    description: Optional[str] = None
    chemical_formula: Optional[str] = None
    molecular_formula: Optional[str] = None
    warnings: List[DrugWarningResponse] = []
    dosage_forms: List[str] = []
    categories: List[str] = []
    atc_codes: List[str] = []
    created_at: datetime

    @classmethod
    def from_orm_drug(cls, drug) -> "DrugDetailResponse":
        return cls(
            id=drug.id,
            generic_name=drug.generic_name,
            description=drug.description,
            chemical_formula=drug.chemical_formula,
            molecular_formula=drug.molecular_formula,
            warnings=[DrugWarningResponse.model_validate(w) for w in drug.warnings],
            dosage_forms=[df.dosage_form for df in drug.dosage_forms],
            categories=[c.category_name for c in drug.categories],
            atc_codes=[a.atc_code for a in drug.atc_codes],
            created_at=drug.created_at,
        )


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
    prediction_count: int = 0
    message: Optional[str] = None
