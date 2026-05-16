from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.redis_client import get_redis
from app.schemas.chatbot import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSendResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    QuickSuggestion,
)
from app.schemas.user import PaginatedResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["🤖 Chatbot tư vấn"])


def _svc(db: AsyncSession, redis: Redis | None = None) -> ChatbotService:
    return ChatbotService(db, redis)


@router.get(
    "/suggestions",
    response_model=list[QuickSuggestion],
    summary="Lấy danh sách câu hỏi gợi ý nhanh",
)
async def get_suggestions():
    return ChatbotService.__new__(ChatbotService).get_quick_suggestions()


@router.post(
    "/message",
    response_model=ChatSendResponse,
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
    redis: Redis = Depends(get_redis),
):
    result = await _svc(db, redis).send_chat_message(
        current_user.id,
        data.session_id,
        data.content,
        request=request,
    )
    await db.commit()
    return result


@router.get(
    "/sessions",
    response_model=list[ChatSessionResponse],
    summary="Danh sách phiên trò chuyện",
)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_sessions(current_user.id)


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phiên trò chuyện mới",
)
async def create_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _svc(db).create_session(current_user.id, data.title)
    await db.commit()
    return result


@router.get(
    "/sessions/{session_id}/messages",
    response_model=PaginatedResponse,
    summary="Tin nhắn trong một phiên trò chuyện",
)
async def get_session_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_history(current_user.id, page, size, session_id)


@router.delete(
    "/sessions/{session_id}",
    summary="Xóa một phiên trò chuyện",
)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_session(current_user.id, session_id)
    await db.commit()
    return {"success": True, "message": "Đã xóa phiên trò chuyện"}


@router.get(
    "/history",
    response_model=PaginatedResponse,
    summary="Lịch sử hội thoại",
)
async def get_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_history(current_user.id, page, size, session_id)


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
