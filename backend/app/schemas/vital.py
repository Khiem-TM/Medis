from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VitalRecordCreate(BaseModel):
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_glucose: Optional[float] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None


class VitalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_glucose: Optional[float] = None
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime
