from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.user import AuthProvider, UserRole


# ── User management ────────────────────────────────────────────────────────

class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    auth_provider: AuthProvider
    is_active: bool
    created_at: datetime


class AdminUserDetail(AdminUserListItem):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    avatar_url: Optional[str] = None
    prescription_count: int = 0
    health_profile_count: int = 0
    activity_log_count: int = 0


class AdminUpdateUser(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ── Drug management ────────────────────────────────────────────────────────

class AdminDrugCreate(BaseModel):
    id: Optional[str] = None
    generic_name: str
    description: Optional[str] = None
    chemical_formula: Optional[str] = None
    molecular_formula: Optional[str] = None


class AdminDrugUpdate(BaseModel):
    generic_name: Optional[str] = None
    description: Optional[str] = None
    chemical_formula: Optional[str] = None
    molecular_formula: Optional[str] = None


class AdminBrandNameCreate(BaseModel):
    name: str
    route: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    country: Optional[str] = None
    image_url: Optional[str] = None


class AdminBrandNameUpdate(BaseModel):
    name: Optional[str] = None
    route: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    country: Optional[str] = None
    image_url: Optional[str] = None


class AdminWarningCreate(BaseModel):
    warning_text: str

    @field_validator("warning_text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Nội dung cảnh báo cần ít nhất 10 ký tự")
        return v


# ── Interaction management ─────────────────────────────────────────────────

class AdminInteractionCreate(BaseModel):
    drug_id: str
    interacts_with_id: str
    interacts_with_name: Optional[str] = None

    @field_validator("interacts_with_id")
    @classmethod
    def validate_different_drugs(cls, v: str, info) -> str:
        if "drug_id" in info.data and v == info.data["drug_id"]:
            raise ValueError("Hai thuốc không được trùng nhau")
        return v


class AdminInteractionUpdate(BaseModel):
    interacts_with_name: Optional[str] = None


# ── Stats ──────────────────────────────────────────────────────────────────

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_drugs: int
    total_interactions: int
    total_prescriptions: int
    active_prescriptions: int
    new_users_today: int
    new_users_this_week: int
    total_chat_messages: int
