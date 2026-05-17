"""
Celery application for scheduled tasks.
Install celery: pip install celery[redis]
"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    from celery.schedules import crontab

    broker_url = getattr(settings, "CELERY_BROKER_URL", "") or settings.REDIS_URL
    backend_url = settings.REDIS_URL

    celery_app = Celery(
        "medis",
        broker=broker_url,
        backend=backend_url,
        include=["app.tasks.reminder_tasks"],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Ho_Chi_Minh",
        enable_utc=True,
        beat_schedule={
            "check-reminders-every-minute": {
                "task": "app.tasks.reminder_tasks.check_due_reminders",
                "schedule": crontab(minute="*"),
            },
            "daily-health-summary": {
                "task": "app.tasks.reminder_tasks.send_daily_summaries",
                "schedule": crontab(hour=20, minute=0),
            },
            "expire-periodic-prescriptions-daily": {
                "task": "app.tasks.reminder_tasks.expire_periodic_prescriptions",
                "schedule": crontab(hour=0, minute=5),
            },
            "mark-missed-intakes-hourly": {
                "task": "app.tasks.reminder_tasks.mark_missed_intakes",
                "schedule": crontab(minute=0),
            },
        },
    )

    CELERY_AVAILABLE = True
    logger.info("Celery initialized successfully")

except ImportError:
    celery_app = None
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed. Scheduled tasks disabled. Install: pip install celery[redis]")
