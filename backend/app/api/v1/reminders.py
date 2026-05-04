from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.reminder_service import ReminderService

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


@router.get("/today", response_model=list[ReminderResponse], summary="Lịch uống thuốc hôm nay")
async def today_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_today_schedule(current_user.id)
