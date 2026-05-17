import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async coroutine from sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _process_due_reminders_async():
    from app.database import AsyncSessionLocal
    from app.services.smart_reminder_service import SmartReminderService
    async with AsyncSessionLocal() as db:
        svc = SmartReminderService(db)
        count = await svc.process_due_reminders()
        logger.info(f"Processed {count} reminders at {datetime.now(timezone.utc)}")
        return count


async def _send_daily_summaries_async():
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.user import User
    from app.services.notification_service import NotificationService
    from app.models.notification import NotificationType, NotificationPriority

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active == True))  # noqa: E712
        users = result.scalars().all()
        count = 0
        for user in users:
            try:
                svc = NotificationService(db)
                await svc.create_and_send(
                    user_id=user.id,
                    type=NotificationType.daily_summary,
                    title="📋 Tóm tắt sức khỏe hôm nay",
                    body=f"Chào {user.full_name or user.username}! Đừng quên kiểm tra lịch uống thuốc và theo dõi sức khỏe hôm nay.",
                    priority=NotificationPriority.low,
                )
                count += 1
            except Exception as e:
                logger.error(f"Daily summary failed for user {user.id}: {e}")
        logger.info(f"Sent daily summaries to {count} users")
        return count


async def _expire_periodic_prescriptions_async():
    """Daily task: mark active periodic prescriptions past end_date as completed."""
    from datetime import date

    from sqlalchemy import select
    from sqlalchemy import update as sql_update

    from app.database import AsyncSessionLocal
    from app.models.notification import NotificationPriority, NotificationType
    from app.models.prescription import MedicationType, Prescription, PrescriptionItem, PrescriptionStatus
    from app.models.reminder import MedicationReminder
    from app.services.notification_service import NotificationService

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Prescription).where(
                Prescription.status == PrescriptionStatus.active,
                Prescription.medication_type == MedicationType.periodic,
                Prescription.end_date < date.today(),
            )
        )
        prescriptions = result.scalars().all()
        count = 0
        for p in prescriptions:
            p.status = PrescriptionStatus.completed

            item_ids_stmt = select(PrescriptionItem.id).where(
                PrescriptionItem.prescription_id == p.id
            )
            await db.execute(
                sql_update(MedicationReminder)
                .where(MedicationReminder.prescription_item_id.in_(item_ids_stmt))
                .values(is_active=False)
            )

            try:
                await NotificationService(db).create_and_send(
                    user_id=p.user_id,
                    type=NotificationType.system,
                    title="Đơn thuốc đã kết thúc",
                    body=f"Đơn thuốc '{p.name}' đã hết hạn và được tự động hoàn thành.",
                    priority=NotificationPriority.medium,
                )
            except Exception as e:
                logger.error(f"Notification failed for prescription {p.id}: {e}")
            count += 1

        await db.commit()
        logger.info(f"Expired {count} periodic prescriptions")
        return count


async def _mark_missed_intakes_async():
    """Hourly task: mark pending intake logs older than 90 min as missed."""
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.intake_log import IntakeStatus, MedicationIntakeLog

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MedicationIntakeLog).where(
                MedicationIntakeLog.status == IntakeStatus.pending
            )
        )
        logs = result.scalars().all()
        cutoff = datetime.now() - timedelta(minutes=90)
        count = 0
        for log in logs:
            scheduled_naive = datetime.combine(log.scheduled_date, log.scheduled_time)
            if scheduled_naive < cutoff:
                log.status = IntakeStatus.missed
                count += 1
        await db.commit()
        logger.info(f"Marked {count} intake logs as missed")
        return count


try:
    from app.celery_app import celery_app, CELERY_AVAILABLE

    if CELERY_AVAILABLE and celery_app:
        @celery_app.task(name="app.tasks.reminder_tasks.check_due_reminders", bind=True, max_retries=3)
        def check_due_reminders(self):
            try:
                return _run_async(_process_due_reminders_async())
            except Exception as exc:
                logger.error(f"check_due_reminders failed: {exc}")
                raise self.retry(exc=exc, countdown=30)

        @celery_app.task(name="app.tasks.reminder_tasks.send_daily_summaries")
        def send_daily_summaries():
            return _run_async(_send_daily_summaries_async())

        @celery_app.task(name="app.tasks.reminder_tasks.expire_periodic_prescriptions")
        def expire_periodic_prescriptions():
            return _run_async(_expire_periodic_prescriptions_async())

        @celery_app.task(name="app.tasks.reminder_tasks.mark_missed_intakes")
        def mark_missed_intakes():
            return _run_async(_mark_missed_intakes_async())

except Exception as e:
    logger.warning(f"Could not register Celery tasks: {e}")


# Standalone async functions for manual triggering (no Celery required)
async def trigger_due_reminders():
    return await _process_due_reminders_async()


async def trigger_daily_summaries():
    return await _send_daily_summaries_async()


async def trigger_expire_periodic_prescriptions():
    return await _expire_periodic_prescriptions_async()


async def trigger_mark_missed_intakes():
    return await _mark_missed_intakes_async()
