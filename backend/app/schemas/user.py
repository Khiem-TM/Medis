from __future__ import annotations

import re
from datetime import date, datetime
from math import ceil
from typing import Generic, List, Optional, TypeVar

from pydantic import (
    BaseModel, ConfigDict, computed_field,
    field_validator, model_validator,
)

from app.models.prescription import PrescriptionStatus
from app.models.user import AuthProvider, UserRole

T = TypeVar("T")


# ── Profile ────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    auth_provider: AuthProvider
    is_active: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        errors = []
        if len(v) < 6:
            errors.append("Password must be at least 6 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            errors.append("Password must contain at least one digit")
        if not re.search(r"[@$!%*?&]", v):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        if errors:
            raise ValueError(" ".join(errors))
        return v

    @model_validator(mode="after")
    def check_passwords(self) -> "ChangePasswordRequest":
        if self.new_password == self.old_password:
            raise ValueError("New password must be different from current password")
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ── Prescription ───────────────────────────────────────────────────────────

class PrescriptionItemCreate(BaseModel):
    drug_id: Optional[str] = None
    drug_name: str
    dosage: str
    frequency: Optional[str] = None
    duration: Optional[str] = None


class PrescriptionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prescription_id: int
    drug_id: Optional[str] = None
    drug_name: str
    dosage: str
    frequency: Optional[str] = None
    duration: Optional[str] = None


class PrescriptionCreate(BaseModel):
    name: str
    notes: Optional[str] = None
    status: Optional[PrescriptionStatus] = PrescriptionStatus.active
    items: List[PrescriptionItemCreate]

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("Prescription must have at least 1 item")
        return v


class PrescriptionUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[PrescriptionStatus] = None
    items: Optional[List[PrescriptionItemCreate]] = None


class PrescriptionListItem(BaseModel):
    """Dùng cho list view — không bao gồm chi tiết items."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: PrescriptionStatus
    drug_count: int = 0  # Set thủ công ở service layer
    created_at: datetime
    updated_at: datetime


class PrescriptionResponse(BaseModel):
    """Chi tiết đầy đủ bao gồm items; drug_count computed từ items."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    status: PrescriptionStatus
    notes: Optional[str] = None
    items: List[PrescriptionItemResponse]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def drug_count(self) -> int:
        return len(self.items)


# ── Health Profile ─────────────────────────────────────────────────────────

class HealthProfileCreate(BaseModel):
    diagnosis_name: str
    exam_date: date
    facility: Optional[str] = None
    doctor: Optional[str] = None
    symptoms: Optional[str] = None
    conclusion: Optional[str] = None
    prescription_id: Optional[int] = None
    notes: Optional[str] = None


class HealthProfileUpdate(BaseModel):
    diagnosis_name: Optional[str] = None
    exam_date: Optional[date] = None
    facility: Optional[str] = None
    doctor: Optional[str] = None
    symptoms: Optional[str] = None
    conclusion: Optional[str] = None
    prescription_id: Optional[int] = None
    notes: Optional[str] = None


class HealthProfileListItem(BaseModel):
    """Dùng cho list view."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    diagnosis_name: str
    exam_date: date
    prescription_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


class HealthProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    diagnosis_name: str
    exam_date: date
    facility: Optional[str] = None
    doctor: Optional[str] = None
    symptoms: Optional[str] = None
    conclusion: Optional[str] = None
    prescription_id: Optional[int] = None
    prescription: Optional[PrescriptionListItem] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ── Shared ─────────────────────────────────────────────────────────────────

class BulkDeleteRequest(BaseModel):
    ids: List[int]


class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    meta: PaginationMeta
