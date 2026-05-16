from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[int] = None

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
    session_id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tiêu đề không được để trống")
        if len(v) > 200:
            raise ValueError("Tiêu đề không vượt quá 200 ký tự")
        return v


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message_count: int = 0
    last_message_preview: Optional[str] = None
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None


class ChatSendResponse(BaseModel):
    session: ChatSessionResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class QuickSuggestion(BaseModel):
    text: str
    category: Literal["drug_usage", "symptom", "interaction"]
