from __future__ import annotations

import json
from math import ceil
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health_baseline import (
    KidneyFunction,
    LiverFunction,
    UserHealthBaseline,
)
from app.models.health_profile import HealthProfile
from app.models.prescription import Prescription, PrescriptionStatus
from app.models.reminder import MedicationReminder
from app.schemas.health import (
    HealthBaselineStructured,
    HealthBaselineUpdate,
    HealthSummaryResponse,
)
from app.schemas.user import HealthProfileListItem, PaginatedResponse, PaginationMeta


def _loads_list(raw: Optional[str]) -> list[Any]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


class HealthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_or_create_baseline(self, user_id: int) -> UserHealthBaseline:
        baseline = await self.db.scalar(
            select(UserHealthBaseline).where(UserHealthBaseline.user_id == user_id)
        )
        if baseline:
            return baseline

        baseline = UserHealthBaseline(user_id=user_id)
        self.db.add(baseline)
        await self.db.flush()
        return baseline

    def _to_structured_baseline(
        self,
        baseline: UserHealthBaseline,
    ) -> HealthBaselineStructured:
        return HealthBaselineStructured(
            id=baseline.id,
            user_id=baseline.user_id,
            height_cm=baseline.height_cm,
            weight_kg=baseline.weight_kg,
            blood_type=baseline.blood_type,
            chronic_conditions=[
                item for item in _loads_list(baseline.chronic_conditions) if isinstance(item, str)
            ],
            allergies=_loads_list(baseline.allergies),
            current_medications=_loads_list(baseline.current_medications),
            is_pregnant=baseline.is_pregnant,
            is_breastfeeding=baseline.is_breastfeeding,
            kidney_function=getattr(baseline.kidney_function, "value", baseline.kidney_function),
            liver_function=getattr(baseline.liver_function, "value", baseline.liver_function),
            health_goals=[
                item for item in _loads_list(baseline.health_goals) if isinstance(item, str)
            ],
            onboarding_completed=baseline.onboarding_completed,
            onboarding_step=baseline.onboarding_step,
            created_at=baseline.created_at,
            updated_at=baseline.updated_at,
        )

    async def get_baseline(self, user_id: int) -> HealthBaselineStructured:
        baseline = await self._get_or_create_baseline(user_id)
        return self._to_structured_baseline(baseline)

    async def update_baseline(
        self,
        user_id: int,
        data: HealthBaselineUpdate,
    ) -> HealthBaselineStructured:
        baseline = await self._get_or_create_baseline(user_id)
        update_data = data.model_dump(exclude_unset=True)

        scalar_fields = {
            "height_cm",
            "weight_kg",
            "blood_type",
            "is_pregnant",
            "is_breastfeeding",
        }
        for field in scalar_fields:
            if field in update_data:
                setattr(baseline, field, update_data[field])

        if "kidney_function" in update_data:
            try:
                baseline.kidney_function = KidneyFunction(update_data["kidney_function"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Chức năng thận không hợp lệ",
                )

        if "liver_function" in update_data:
            try:
                baseline.liver_function = LiverFunction(update_data["liver_function"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Chức năng gan không hợp lệ",
                )

        if "chronic_conditions" in update_data:
            baseline.chronic_conditions = json.dumps(
                update_data["chronic_conditions"] or [],
                ensure_ascii=False,
            )
        if "allergies" in update_data:
            baseline.allergies = json.dumps(
                [item.model_dump() for item in data.allergies or []],
                ensure_ascii=False,
            )
        if "current_medications" in update_data:
            baseline.current_medications = json.dumps(
                [item.model_dump() for item in data.current_medications or []],
                ensure_ascii=False,
            )
        if "health_goals" in update_data:
            baseline.health_goals = json.dumps(
                update_data["health_goals"] or [],
                ensure_ascii=False,
            )

        baseline.onboarding_step = max(baseline.onboarding_step, 3)
        baseline.onboarding_completed = True

        await self.db.flush()
        await self.db.refresh(baseline)
        return self._to_structured_baseline(baseline)

    async def get_summary(self, user_id: int) -> HealthSummaryResponse:
        baseline = await self._get_or_create_baseline(user_id)

        recent_visits_result = await self.db.execute(
            select(HealthProfile)
            .where(HealthProfile.user_id == user_id)
            .order_by(HealthProfile.exam_date.desc())
            .limit(5)
        )
        recent_visits = recent_visits_result.scalars().all()

        total_visits = await self.db.scalar(
            select(func.count(HealthProfile.id)).where(HealthProfile.user_id == user_id)
        )
        active_prescriptions = await self.db.scalar(
            select(func.count(Prescription.id)).where(
                Prescription.user_id == user_id,
                Prescription.status == PrescriptionStatus.active,
            )
        )
        active_reminders = await self.db.scalar(
            select(func.count(MedicationReminder.id)).where(
                MedicationReminder.user_id == user_id,
                MedicationReminder.is_active == True,  # noqa: E712
            )
        )

        return HealthSummaryResponse(
            baseline=self._to_structured_baseline(baseline),
            recent_visits=[HealthProfileListItem.model_validate(item) for item in recent_visits],
            total_visits=total_visits or 0,
            active_prescriptions=active_prescriptions or 0,
            active_reminders=active_reminders or 0,
            last_exam_date=recent_visits[0].exam_date if recent_visits else None,
        )

    async def list_visits(
        self,
        user_id: int,
        page: int,
        size: int,
        search: Optional[str] = None,
        exam_date_from=None,
        exam_date_to=None,
    ) -> PaginatedResponse:
        stmt = select(HealthProfile).where(HealthProfile.user_id == user_id)

        if search:
            stmt = stmt.where(HealthProfile.diagnosis_name.ilike(f"%{search}%"))
        if exam_date_from:
            stmt = stmt.where(HealthProfile.exam_date >= exam_date_from)
        if exam_date_to:
            stmt = stmt.where(HealthProfile.exam_date <= exam_date_to)

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))

        result = await self.db.execute(
            stmt.order_by(HealthProfile.exam_date.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        visits = result.scalars().all()

        return PaginatedResponse(
            items=[HealthProfileListItem.model_validate(item) for item in visits],
            meta=PaginationMeta(
                total=total or 0,
                page=page,
                size=size,
                total_pages=max(1, ceil((total or 0) / size)),
            ),
        )
