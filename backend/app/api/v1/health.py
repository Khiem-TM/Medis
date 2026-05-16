from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.health import (
    HealthBaselineStructured,
    HealthBaselineUpdate,
    HealthSummaryResponse,
)
from app.schemas.user import HealthProfileCreate, HealthProfileResponse
from app.services.health_service import HealthService
from app.services.user_service import HealthProfileService

router = APIRouter(prefix="/users/me/health", tags=["🏥 Hồ sơ sức khỏe người dùng"])


def _health_svc(db: AsyncSession) -> HealthService:
    return HealthService(db)


@router.get(
    "/summary",
    response_model=HealthSummaryResponse,
    summary="Tổng quan hồ sơ sức khỏe người dùng",
)
async def get_health_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _health_svc(db).get_summary(current_user.id)


@router.get(
    "/baseline",
    response_model=HealthBaselineStructured,
    summary="Lấy dữ liệu sức khỏe nền đã chuẩn hóa",
)
async def get_health_baseline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _health_svc(db).get_baseline(current_user.id)
    await db.commit()
    return result


@router.put(
    "/baseline",
    response_model=HealthBaselineStructured,
    summary="Cập nhật dữ liệu sức khỏe nền",
)
async def update_health_baseline(
    data: HealthBaselineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _health_svc(db).update_baseline(current_user.id, data)
    await db.commit()
    return result


@router.get(
    "/visits",
    summary="Danh sách lịch sử khám bệnh",
)
async def list_health_visits(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Tìm theo tên bệnh / chẩn đoán"),
    exam_date_from: Optional[date] = Query(None, description="Lọc từ ngày khám"),
    exam_date_to: Optional[date] = Query(None, description="Lọc đến ngày khám"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _health_svc(db).list_visits(
        current_user.id,
        page,
        size,
        search,
        exam_date_from,
        exam_date_to,
    )


@router.post(
    "/visits",
    response_model=HealthProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo lần khám mới trong hồ sơ sức khỏe",
)
async def create_health_visit(
    data: HealthProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await HealthProfileService(db).create(current_user.id, data)
    await db.commit()
    return result
