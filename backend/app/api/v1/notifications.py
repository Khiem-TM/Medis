import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AsyncSessionLocal
from app.api.deps import get_current_user
from app.models.user import User
from app.core.ws_manager import ws_manager
from app.core.security import decode_token
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationResponse, NotificationListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["🔔 Thông báo"])


def _svc(db: AsyncSession) -> NotificationService:
    return NotificationService(db)


@router.websocket("/ws")
async def notification_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """WebSocket endpoint. Connect: ws://host/api/v1/notifications/ws?token=<access_token>"""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    user_id = int(payload.get("sub", 0))
    if not user_id:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected", "user_id": user_id})
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "mark_read":
                notif_id = data.get("notification_id")
                if notif_id:
                    async with AsyncSessionLocal() as db:
                        await NotificationService(db).mark_read(notif_id, user_id)
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WS error user={user_id}: {e}")
        ws_manager.disconnect(user_id, websocket)


@router.get("", response_model=NotificationListResponse, summary="Danh sách thông báo")
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_notifications(current_user.id, page, size, unread_only)


@router.patch("/{notification_id}/read", summary="Đánh dấu đã đọc")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await _svc(db).mark_read(notification_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông báo")
    return {"message": "Đã đánh dấu đã đọc"}


@router.patch("/read-all", summary="Đánh dấu tất cả đã đọc")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await _svc(db).mark_all_read(current_user.id)
    return {"message": f"Đã đánh dấu {count} thông báo đã đọc"}


@router.get("/online-status", summary="Kiểm tra trạng thái online (admin debug)")
async def online_status(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "is_online": ws_manager.is_online(current_user.id),
    }
