from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake_log import IntakeStatus, MedicationIntakeLog
from app.models.reminder import MedicationReminder
from app.schemas.intake import (
    ConfirmIntakeRequest,
    DayStats,
    IntakeStatsResponse,
    MedicationIntakeLogResponse,
)
from app.schemas.user import PaginatedResponse, PaginationMeta

logger = logging.getLogger(__name__)

LATE_THRESHOLD_MINUTES = 30


class MedicationTrackingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_today_log(
        self, user_id: int, reminder_id: int
    ) -> MedicationIntakeLog:
        """Idempotent: trả về log hôm nay cho reminder hoặc tạo mới với status=pending."""
        today = date.today()
        result = await self.db.execute(
            select(MedicationIntakeLog).where(
                and_(
                    MedicationIntakeLog.reminder_id == reminder_id,
                    MedicationIntakeLog.scheduled_date == today,
                )
            )
        )
        log = result.scalar_one_or_none()
        if log:
            return log

        reminder = await self.db.scalar(
            select(MedicationReminder).where(MedicationReminder.id == reminder_id)
        )
        if not reminder or reminder.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Nhắc nhở không tìm thấy")

        log = MedicationIntakeLog(
            user_id=user_id,
            reminder_id=reminder_id,
            prescription_item_id=reminder.prescription_item_id,
            drug_name=reminder.drug_name,
            scheduled_date=today,
            scheduled_time=reminder.reminder_time,
            status=IntakeStatus.pending,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def confirm_intake(
        self, user_id: int, reminder_id: int, data: ConfirmIntakeRequest
    ) -> MedicationIntakeLogResponse:
        """Người dùng xác nhận đã uống thuốc; xác định taken vs late."""
        reminder = await self.db.scalar(
            select(MedicationReminder).where(MedicationReminder.id == reminder_id)
        )
        if not reminder or reminder.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Nhắc nhở không tìm thấy")

        log = await self.get_or_create_today_log(user_id, reminder_id)

        if log.status in (IntakeStatus.taken, IntakeStatus.late):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Đã xác nhận uống thuốc này rồi")

        now = datetime.now(timezone.utc)
        scheduled_naive = datetime.combine(log.scheduled_date, log.scheduled_time)
        delta_minutes = (now.replace(tzinfo=None) - scheduled_naive).total_seconds() / 60
        new_status = IntakeStatus.late if delta_minutes > LATE_THRESHOLD_MINUTES else IntakeStatus.taken

        log.status = new_status
        log.taken_at = now
        log.notes = data.notes

        await self.db.commit()
        await self.db.refresh(log)
        logger.info(f"Intake confirmed: user={user_id} reminder={reminder_id} status={new_status}")
        return MedicationIntakeLogResponse.model_validate(log)

    async def get_stats(self, user_id: int, period: str = "week") -> IntakeStatsResponse:
        """Tính tỉ lệ tuân thủ uống thuốc trong 7 hoặc 30 ngày gần nhất."""
        days = 7 if period == "week" else 30
        start = date.today() - timedelta(days=days - 1)

        result = await self.db.execute(
            select(MedicationIntakeLog).where(
                and_(
                    MedicationIntakeLog.user_id == user_id,
                    MedicationIntakeLog.scheduled_date >= start,
                    MedicationIntakeLog.scheduled_date <= date.today(),
                )
            ).order_by(MedicationIntakeLog.scheduled_date)
        )
        logs = result.scalars().all()

        total = len(logs)
        taken_count = sum(1 for lg in logs if lg.status in (IntakeStatus.taken, IntakeStatus.late))
        on_time_count = sum(1 for lg in logs if lg.status == IntakeStatus.taken)
        missed_count = sum(1 for lg in logs if lg.status == IntakeStatus.missed)
        pending_count = sum(1 for lg in logs if lg.status == IntakeStatus.pending)

        adherence = taken_count / total if total > 0 else 0.0
        on_time = on_time_count / total if total > 0 else 0.0

        day_map: dict[date, dict] = defaultdict(lambda: {"scheduled": 0, "taken": 0, "missed": 0})
        for lg in logs:
            day_map[lg.scheduled_date]["scheduled"] += 1
            if lg.status in (IntakeStatus.taken, IntakeStatus.late):
                day_map[lg.scheduled_date]["taken"] += 1
            elif lg.status == IntakeStatus.missed:
                day_map[lg.scheduled_date]["missed"] += 1

        by_day = [DayStats(date=d, **stats) for d, stats in sorted(day_map.items())]

        return IntakeStatsResponse(
            period=period,
            total_scheduled=total,
            total_taken=taken_count,
            total_missed=missed_count,
            total_pending=pending_count,
            adherence_rate=round(adherence, 4),
            on_time_rate=round(on_time, 4),
            by_day=by_day,
        )

    async def get_history(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PaginatedResponse:
        stmt = (
            select(MedicationIntakeLog)
            .where(MedicationIntakeLog.user_id == user_id)
            .order_by(
                MedicationIntakeLog.scheduled_date.desc(),
                MedicationIntakeLog.scheduled_time.desc(),
            )
        )
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.offset((page - 1) * size).limit(size))
        logs = result.scalars().all()

        return PaginatedResponse(
            items=[MedicationIntakeLogResponse.model_validate(lg) for lg in logs],
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )
