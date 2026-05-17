from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.intake import IntakeStatsResponse, MedicationIntakeLogResponse
from app.services.tracking_service import MedicationTrackingService

router = APIRouter(prefix="/users/me/intakes", tags=["📊 Lịch sử uống thuốc"])


@router.get("/stats", response_model=IntakeStatsResponse, summary="Thống kê tuân thủ uống thuốc")
async def get_intake_stats(
    period: str = Query("week", pattern="^(today|week|month)$", description="Khoảng thời gian: today | week (7 ngày) | month (30 ngày)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MedicationTrackingService(db).get_stats(current_user.id, period)


@router.get("/date/{target_date}", response_model=list[MedicationIntakeLogResponse], summary="Lịch sử uống thuốc theo ngày")
async def get_intakes_by_date(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MedicationTrackingService(db).get_logs_for_date(current_user.id, target_date)


@router.get("/history", summary="Lịch sử uống thuốc")
async def get_intake_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MedicationTrackingService(db).get_history(current_user.id, page, size)
