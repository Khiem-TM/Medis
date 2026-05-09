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

except Exception as e:
    logger.warning(f"Could not register Celery tasks: {e}")


# Standalone async functions for manual triggering (no Celery required)
async def trigger_due_reminders():
    return await _process_due_reminders_async()


async def trigger_daily_summaries():
    return await _send_daily_summaries_async()
