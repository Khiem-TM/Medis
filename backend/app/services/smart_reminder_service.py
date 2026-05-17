import logging
from datetime import datetime, timezone, time as time_type
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.reminder import MedicationReminder
from app.models.notification import NotificationType, NotificationPriority
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

PRIORITY_MESSAGES = {
    1: ("Nhắc nhở uống thuốc", "Đến giờ uống {drug_name} rồi! 💊"),
    2: ("Bạn chưa uống thuốc", "Bạn chưa uống {drug_name}. Hãy uống ngay nhé! ⚠️"),
    3: ("Quan trọng: Chưa uống thuốc", "Bạn đã bỏ lỡ {drug_name} hơn 1 tiếng. Hãy uống ngay hoặc bỏ qua liều này. 🚨"),
}


class SmartReminderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notif_svc = NotificationService(db)

    def _is_reminder_due_today(self, reminder: MedicationReminder) -> bool:
        today_abbr = DAY_MAP[datetime.now().weekday()]
        if reminder.frequency == "daily":
            return True
        if reminder.days_of_week and today_abbr in reminder.days_of_week.lower():
            return True
        return False

    async def get_due_reminders(self) -> list[MedicationReminder]:
        """Return all active reminders due within the current minute."""
        now = datetime.now()
        current_time = time_type(now.hour, now.minute)
        result = await self.db.execute(
            select(MedicationReminder).where(
                and_(
                    MedicationReminder.is_active == True,  # noqa: E712
                    MedicationReminder.reminder_time == current_time,
                )
            )
        )
        reminders = result.scalars().all()
        return [r for r in reminders if self._is_reminder_due_today(r)]

    async def send_reminder_notification(
        self,
        reminder: MedicationReminder,
        escalation_level: int = 1,
    ) -> None:
        """Send a medication reminder notification with escalation support."""
        title_template, body_template = PRIORITY_MESSAGES.get(
            escalation_level, PRIORITY_MESSAGES[1]
        )
        priority = (
            NotificationPriority.high if escalation_level >= 2 else NotificationPriority.medium
        )
        if escalation_level >= 3:
            priority = NotificationPriority.urgent

        await self.notif_svc.create_and_send(
            user_id=reminder.user_id,
            type=NotificationType.medication_reminder,
            title=title_template,
            body=body_template.format(drug_name=reminder.drug_name),
            priority=priority,
            data={
                "reminder_id": reminder.id,
                "drug_name": reminder.drug_name,
                "reminder_time": reminder.reminder_time.strftime("%H:%M"),
                "escalation_level": escalation_level,
            },
            reminder_id=reminder.id,
        )
        logger.info(
            f"Reminder sent: user={reminder.user_id}, drug={reminder.drug_name}, level={escalation_level}"
        )
        await self._ensure_intake_log(reminder)

    async def _ensure_intake_log(self, reminder: MedicationReminder) -> None:
        """Tạo pending intake log khi reminder nổ, idempotent, best-effort."""
        from app.services.tracking_service import MedicationTrackingService
        try:
            await MedicationTrackingService(self.db).get_or_create_today_log(
                reminder.user_id, reminder.id
            )
        except Exception as e:
            logger.warning(f"Could not create intake log for reminder {reminder.id}: {e}")

    async def process_due_reminders(self) -> int:
        """Process all due reminders. Called by scheduler every minute."""
        due = await self.get_due_reminders()
        count = 0
        for reminder in due:
            try:
                await self.send_reminder_notification(reminder, escalation_level=1)
                count += 1
            except Exception as e:
                logger.error(f"Failed to send reminder {reminder.id}: {e}")
        return count
