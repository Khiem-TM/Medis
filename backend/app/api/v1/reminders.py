from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.intake import ConfirmIntakeRequest, MedicationIntakeLogResponse
from app.schemas.reminder import ReminderCreate, ReminderResponse, ReminderUpdate
from app.services.reminder_service import ReminderService
from app.services.tracking_service import MedicationTrackingService

router = APIRouter(prefix="/users/me/reminders", tags=["💊 Nhắc nhở thuốc"])


def _svc(db: AsyncSession) -> ReminderService:
    return ReminderService(db)


@router.get("", response_model=list[ReminderResponse], summary="Danh sách nhắc nhở thuốc")
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list(current_user.id)


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED, summary="Tạo nhắc nhở thuốc")
async def create_reminder(
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).create(current_user.id, data)


@router.put("/{reminder_id}", response_model=ReminderResponse, summary="Cập nhật nhắc nhở thuốc")
async def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _svc(db).update(reminder_id, current_user.id, data)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhắc nhở")
    return result


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa nhắc nhở thuốc")
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await _svc(db).delete(reminder_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhắc nhở")


@router.get("/today", response_model=list[ReminderResponse], summary="Lịch uống thuốc theo ngày")
async def today_schedule(
    target_date: date = Query(default=None, description="Ngày cần xem (YYYY-MM-DD). Mặc định: hôm nay"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if target_date:
        return await _svc(db).get_schedule_for_date(current_user.id, target_date)
    return await _svc(db).get_today_schedule(current_user.id)


@router.post(
    "/{reminder_id}/confirm",
    response_model=MedicationIntakeLogResponse,
    summary="Xác nhận đã uống thuốc",
    description="Ghi nhận taken (≤30 phút) hoặc late (>30 phút so với giờ nhắc).",
)
async def confirm_intake(
    reminder_id: int,
    data: ConfirmIntakeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MedicationTrackingService(db).confirm_intake(current_user.id, reminder_id, data)
