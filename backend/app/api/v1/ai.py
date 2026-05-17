from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.schemas.ai import AiChatRequest, AiChatResponse
from app.services.gemini_client import build_gemini_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-chat", tags=["🤖 Gemini AI"])

_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI của Medis. Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu. "
    "Không chẩn đoán chắc chắn, không kê đơn bắt buộc, và luôn khuyên người dùng "
    "tham khảo bác sĩ hoặc dược sĩ khi câu hỏi liên quan đến sức khỏe, thuốc hoặc triệu chứng."
)


@router.post(
    "",
    response_model=AiChatResponse,
    summary="Gửi tin nhắn tới Gemini qua backend",
    description="Frontend gọi endpoint nội bộ này; API key Gemini chỉ được dùng ở backend.",
)
async def ai_chat(
    data: AiChatRequest,
    current_user: User = Depends(get_current_user),
):
    client = build_gemini_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ Gemini chưa được cấu hình",
        )

    try:
        reply = await client.generate_text(
            _SYSTEM_PROMPT,
            [{"role": "user", "content": data.message}],
            max_tokens=800,
            temperature=0.7,
        )
    except Exception as exc:
        logger.warning("Gemini ai-chat request failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Không thể kết nối Gemini, vui lòng thử lại sau",
        ) from exc

    return AiChatResponse(reply=reply, model=settings.GEMINI_MODEL)
