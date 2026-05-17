from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vital_record import VitalRecord
from app.schemas.vital import VitalRecordCreate, VitalRecordResponse


class VitalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_latest(self, user_id: int) -> Optional[VitalRecordResponse]:
        result = await self.db.execute(
            select(VitalRecord)
            .where(VitalRecord.user_id == user_id)
            .order_by(VitalRecord.recorded_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        return VitalRecordResponse.model_validate(record) if record else None

    async def list_recent(self, user_id: int, limit: int = 30) -> list[VitalRecordResponse]:
        result = await self.db.execute(
            select(VitalRecord)
            .where(VitalRecord.user_id == user_id)
            .order_by(VitalRecord.recorded_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()
        return [VitalRecordResponse.model_validate(r) for r in records]

    async def create(self, user_id: int, data: VitalRecordCreate) -> VitalRecordResponse:
        recorded_at = data.recorded_at or datetime.now(timezone.utc)
        record = VitalRecord(
            user_id=user_id,
            heart_rate=data.heart_rate,
            systolic_bp=data.systolic_bp,
            diastolic_bp=data.diastolic_bp,
            blood_glucose=data.blood_glucose,
            notes=data.notes,
            recorded_at=recorded_at,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return VitalRecordResponse.model_validate(record)
