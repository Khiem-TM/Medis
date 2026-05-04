from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import MedicationReminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse

# Day abbreviations for filtering
DAY_MAP = {
    0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun",
}


def _to_response(reminder: MedicationReminder) -> ReminderResponse:
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        prescription_item_id=reminder.prescription_item_id,
        drug_name=reminder.drug_name,
        reminder_time=reminder.reminder_time.strftime("%H:%M"),
        frequency=reminder.frequency,
        days_of_week=reminder.days_of_week,
        is_active=reminder.is_active,
        notes=reminder.notes,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )


class ReminderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, user_id: int) -> List[ReminderResponse]:
        result = await self.db.execute(
            select(MedicationReminder)
            .where(MedicationReminder.user_id == user_id)
            .order_by(MedicationReminder.reminder_time)
        )
        reminders = result.scalars().all()
        return [_to_response(r) for r in reminders]

    async def create(self, user_id: int, data: ReminderCreate) -> ReminderResponse:
        reminder_time = time.fromisoformat(data.reminder_time)
        reminder = MedicationReminder(
            user_id=user_id,
            prescription_item_id=data.prescription_item_id,
            drug_name=data.drug_name,
            reminder_time=reminder_time,
            frequency=data.frequency,
            days_of_week=data.days_of_week,
            is_active=True,
            notes=data.notes,
        )
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return _to_response(reminder)

    async def update(self, reminder_id: int, user_id: int, data: ReminderUpdate) -> Optional[ReminderResponse]:
        result = await self.db.execute(
            select(MedicationReminder).where(
                and_(
                    MedicationReminder.id == reminder_id,
                    MedicationReminder.user_id == user_id,
                )
            )
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return None

        if data.drug_name is not None:
            reminder.drug_name = data.drug_name.strip()
        if data.reminder_time is not None:
            reminder.reminder_time = time.fromisoformat(data.reminder_time)
        if data.frequency is not None:
            reminder.frequency = data.frequency
        if data.days_of_week is not None:
            reminder.days_of_week = data.days_of_week
        if data.is_active is not None:
            reminder.is_active = data.is_active
        if data.notes is not None:
            reminder.notes = data.notes

        await self.db.commit()
        await self.db.refresh(reminder)
        return _to_response(reminder)

    async def delete(self, reminder_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(MedicationReminder).where(
                and_(
                    MedicationReminder.id == reminder_id,
                    MedicationReminder.user_id == user_id,
                )
            )
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return False
        await self.db.delete(reminder)
        await self.db.commit()
        return True

    async def get_today_schedule(self, user_id: int) -> List[ReminderResponse]:
        today_abbr = DAY_MAP[datetime.now().weekday()]
        result = await self.db.execute(
            select(MedicationReminder).where(
                and_(
                    MedicationReminder.user_id == user_id,
                    MedicationReminder.is_active == True,  # noqa: E712
                )
            ).order_by(MedicationReminder.reminder_time)
        )
        reminders = result.scalars().all()

        filtered = []
        for r in reminders:
            if r.frequency == "daily":
                filtered.append(r)
            elif r.days_of_week and today_abbr in r.days_of_week.lower():
                filtered.append(r)

        return [_to_response(r) for r in filtered]
