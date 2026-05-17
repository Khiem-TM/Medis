from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.vital import VitalRecordCreate, VitalRecordResponse
from app.services.vital_service import VitalService

router = APIRouter(prefix="/users/me/vitals", tags=["❤️ Chỉ số sức khoẻ"])


@router.get("/latest", response_model=VitalRecordResponse | None, summary="Chỉ số sức khoẻ mới nhất")
async def get_latest_vital(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VitalService(db).get_latest(current_user.id)


@router.get("", response_model=list[VitalRecordResponse], summary="Lịch sử chỉ số sức khoẻ")
async def list_vitals(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VitalService(db).list_recent(current_user.id, limit)


@router.post("", response_model=VitalRecordResponse, status_code=201, summary="Ghi nhận chỉ số sức khoẻ")
async def create_vital(
    data: VitalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VitalService(db).create(current_user.id, data)
