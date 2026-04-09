from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

_ACTION_MAP: dict[str, str] = {
    "LOGIN": "Đăng nhập",
    "LOGOUT": "Đăng xuất",
    "REGISTER": "Đăng ký tài khoản",
    "PROFILE_UPDATE": "Cập nhật hồ sơ",
    "PASSWORD_CHANGE": "Đổi mật khẩu",
    "DRUG_SEARCH": "Tra cứu thuốc",
    "INTERACTION_CHECK": "Kiểm tra tương tác thuốc",
    "PRESCRIPTION_CREATE": "Tạo đơn thuốc",
    "PRESCRIPTION_UPDATE": "Cập nhật đơn thuốc",
    "PRESCRIPTION_DELETE": "Xóa đơn thuốc",
    "HEALTH_PROFILE_CREATE": "Tạo hồ sơ bệnh án",
    "HEALTH_PROFILE_UPDATE": "Cập nhật hồ sơ bệnh án",
    "HEALTH_PROFILE_DELETE": "Xóa hồ sơ bệnh án",
    "CHATBOT_MESSAGE": "Tư vấn chatbot",
}


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    detail: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime

    @computed_field
    @property
    def action_display(self) -> str:
        return _ACTION_MAP.get(self.action, self.action)


class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    source: str
    message: str
    detail: Optional[Any] = None
    created_at: datetime


class DeleteManyRequest(BaseModel):
    ids: List[int] = []

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: List[int]) -> List[int]:
        if len(v) > 100:
            raise ValueError("Tối đa 100 bản ghi mỗi lần xóa")
        return v
