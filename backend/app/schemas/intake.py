from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.intake_log import IntakeStatus


class MedicationIntakeLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    reminder_id: Optional[int] = None
    prescription_item_id: Optional[int] = None
    drug_name: str
    scheduled_date: date
    scheduled_time: time
    status: IntakeStatus
    taken_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


class ConfirmIntakeRequest(BaseModel):
    notes: Optional[str] = None


class DayStats(BaseModel):
    date: date
    scheduled: int
    taken: int
    missed: int


class IntakeStatsResponse(BaseModel):
    period: str
    total_scheduled: int
    total_taken: int
    total_missed: int
    total_pending: int
    adherence_rate: float
    on_time_rate: float
    by_day: list[DayStats]
