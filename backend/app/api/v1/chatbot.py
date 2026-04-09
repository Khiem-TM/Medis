from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.chatbot import ChatMessageCreate, ChatMessageResponse, QuickSuggestion
from app.schemas.user import PaginatedResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["🤖 Chatbot tư vấn"])


def _svc(db: AsyncSession) -> ChatbotService:
    return ChatbotService(db)


@router.get(
    "/suggestions",
    response_model=list[QuickSuggestion],
    summary="Lấy danh sách câu hỏi gợi ý nhanh",
)
async def get_suggestions():
    return ChatbotService.__new__(ChatbotService).get_quick_suggestions()


@router.post(
    "/message",
    summary="Gửi tin nhắn và nhận phản hồi từ AI",
    description=(
        "Gửi câu hỏi về sức khỏe, thuốc hoặc triệu chứng. "
        "AI sẽ trả lời dựa trên hồ sơ sức khỏe của bạn."
    ),
)
async def send_message(
    data: ChatMessageCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reply = await _svc(db).send_message(current_user.id, data.content, request)
    await db.commit()
    return {
        "success": True,
        "message": "Đã nhận phản hồi từ AI",
        "data": reply.model_dump(),
    }


@router.get(
    "/history",
    response_model=PaginatedResponse,
    summary="Lịch sử hội thoại",
)
async def get_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_history(current_user.id, page, size)


@router.delete(
    "/history",
    summary="Xóa toàn bộ lịch sử hội thoại",
)
async def delete_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    n = await _svc(db).delete_history(current_user.id)
    await db.commit()
    return {"success": True, "message": f"Đã xóa {n} tin nhắn", "data": {"deleted": n}}
