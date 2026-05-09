from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.onboarding_service import OnboardingService
from app.schemas.onboarding import (
    OnboardingStep1Request, OnboardingStep2Request, OnboardingStep3Request,
    HealthBaselineResponse, ParsedConditionsResponse,
)

router = APIRouter(prefix="/users/me/onboarding", tags=["🏥 Onboarding hồ sơ sức khỏe"])


def _svc(db: AsyncSession) -> OnboardingService:
    return OnboardingService(db)


@router.get("", response_model=HealthBaselineResponse, summary="Lấy trạng thái onboarding")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_status(current_user.id)


@router.post(
    "/step1",
    response_model=HealthBaselineResponse,
    summary="Bước 1: Thông tin sức khỏe cơ bản",
)
async def onboarding_step1(
    data: OnboardingStep1Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).save_step1(current_user.id, data)


@router.post(
    "/step2",
    response_model=HealthBaselineResponse,
    summary="Bước 2: Bệnh nền & dị ứng thuốc (hỗ trợ nhập text tự do)",
)
async def onboarding_step2(
    data: OnboardingStep2Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).save_step2(current_user.id, data)


@router.post(
    "/step3",
    response_model=HealthBaselineResponse,
    summary="Bước 3: Thuốc đang dùng & mục tiêu sức khỏe",
)
async def onboarding_step3(
    data: OnboardingStep3Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).save_step3(current_user.id, data)


@router.post(
    "/parse-text",
    response_model=ParsedConditionsResponse,
    summary="Parse văn bản sức khỏe tiếng Việt bằng AI",
)
async def parse_health_text(
    text: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    return await svc.parse_conditions_with_ai(text)
