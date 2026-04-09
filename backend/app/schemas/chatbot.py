from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ChatMessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nội dung tin nhắn không được để trống")
        if len(v) > 2000:
            raise ValueError("Nội dung tin nhắn không vượt quá 2000 ký tự")
        return v


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class QuickSuggestion(BaseModel):
    text: str
    category: Literal["drug_usage", "symptom", "interaction"]
