from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, field_validator


class ReminderCreate(BaseModel):
    drug_name: str
    reminder_time: str  # "HH:MM"
    frequency: str = "daily"
    days_of_week: Optional[str] = None
    prescription_item_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("drug_name")
    @classmethod
    def validate_drug_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên thuốc không được để trống")
        if len(v) > 200:
            raise ValueError("Tên thuốc không vượt quá 200 ký tự")
        return v

    @field_validator("reminder_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        try:
            time.fromisoformat(v)
        except ValueError:
            raise ValueError("Thời gian không hợp lệ (HH:MM)")
        return v


class ReminderUpdate(BaseModel):
    drug_name: Optional[str] = None
    reminder_time: Optional[str] = None
    frequency: Optional[str] = None
    days_of_week: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ReminderResponse(BaseModel):
    id: int
    user_id: int
    prescription_item_id: Optional[int]
    drug_name: str
    reminder_time: str
    frequency: str
    days_of_week: Optional[str]
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
