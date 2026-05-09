import json
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.core.ws_manager import ws_manager
from app.schemas.notification import NotificationResponse, NotificationListResponse

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_and_send(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.medium,
        data: Optional[dict] = None,
        reminder_id: Optional[int] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            priority=priority,
            title=title,
            body=body,
            data=json.dumps(data, ensure_ascii=False) if data else None,
            reminder_id=reminder_id,
            scheduled_at=datetime.now(timezone.utc),
        )
        self.db.add(notif)
        await self.db.flush()

        # Attempt real-time WebSocket delivery
        delivered = await ws_manager.send_to_user(user_id, {
            "type": "notification",
            "payload": {
                "id": notif.id,
                "notification_type": type.value,
                "priority": priority.value,
                "title": title,
                "body": body,
                "data": data,
                "reminder_id": reminder_id,
            }
        })

        if delivered:
            notif.sent_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def list_notifications(
        self, user_id: int, page: int = 1, size: int = 20, unread_only: bool = False
    ) -> NotificationListResponse:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712
        query = query.order_by(Notification.created_at.desc())

        count_q = select(func.count()).select_from(
            select(Notification).where(Notification.user_id == user_id).subquery()
        )
        unread_q = select(func.count()).select_from(
            select(Notification).where(
                Notification.user_id == user_id, Notification.is_read == False  # noqa: E712
            ).subquery()
        )

        total_result = await self.db.execute(count_q)
        unread_result = await self.db.execute(unread_q)
        total = total_result.scalar_one()
        unread_count = unread_result.scalar_one()

        paginated = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(paginated)
        items = result.scalars().all()

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            unread_count=unread_count,
        )

    async def mark_read(self, notification_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return False
        notif.is_read = True
        await self.db.commit()
        return True

    async def mark_all_read(self, user_id: int) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount
