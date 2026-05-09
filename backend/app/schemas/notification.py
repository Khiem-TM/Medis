import json
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, model_validator
from app.models.notification import NotificationType, NotificationPriority


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    type: NotificationType
    priority: NotificationPriority
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool
    reminder_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def parse_data_json(cls, values: Any) -> Any:
        if hasattr(values, "__dict__"):
            values = values.__dict__
        if isinstance(values, dict) and isinstance(values.get("data"), str):
            try:
                values["data"] = json.loads(values["data"])
            except (json.JSONDecodeError, TypeError):
                values["data"] = None
        return values


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
