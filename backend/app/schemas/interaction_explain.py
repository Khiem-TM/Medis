from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InteractionExplainRequest(BaseModel):
    drug_id_1: str
    drug_id_2: str


class InteractionExplainResponse(BaseModel):
    drug_a_id: str
    drug_b_id: str
    drug_a_name: str
    drug_b_name: str
    severity: Literal["Nghiêm trọng", "Cần chú ý", "Nhẹ"]
    severity_color: Literal["red", "amber", "yellow"]
    summary: str = Field(description="Tóm tắt 1 câu, tối đa 120 ký tự")
    mechanism: str = Field(description="Giải thích cơ chế bằng ngôn ngữ đơn giản, 2-3 câu")
    symptoms_to_watch: list[str] = Field(description="Các triệu chứng cần theo dõi")
    what_to_do: list[str] = Field(description="Hành động khuyến nghị")
    when_to_see_doctor: str = Field(description="Mô tả tình huống cần gặp bác sĩ")
    can_be_used_together: bool | None = Field(description="True=có thể dùng, False=tránh dùng, None=tuỳ tình huống")
    confidence_note: str | None = Field(default=None, description="Ghi chú độ tin cậy nếu nguồn là model_predicted")
    source: str
    from_cache: bool = False
    disclaimer: str = "Thông tin này chỉ mang tính tham khảo dược học. Luôn tham khảo ý kiến bác sĩ hoặc dược sĩ trước khi thay đổi thuốc."
