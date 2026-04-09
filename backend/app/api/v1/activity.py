from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.log import ActivityLogResponse, DeleteManyRequest
from app.schemas.user import PaginatedResponse
from app.services.log_service import ActivityLogService

router = APIRouter(prefix="/activity", tags=["📋 Lịch sử hoạt động"])


def _svc(db: AsyncSession) -> ActivityLogService:
    return ActivityLogService(db)


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Xem lịch sử hoạt động",
    description=(
        "Danh sách các thao tác đã thực hiện trên hệ thống. "
        "Có thể lọc theo loại hoạt động, từ khóa và khoảng thời gian."
    ),
)
async def get_history(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    action: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_user_history(
        current_user.id, page, size, action, keyword, date_from, date_to
    )


@router.get(
    "/export",
    summary="Xuất lịch sử ra file Excel",
)
async def export_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await _svc(db).export_xlsx(user_id=current_user.id)
    filename = f"lich-su-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete(
    "/{log_id}",
    summary="Xóa một bản ghi lịch sử",
)
async def delete_one(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_one(current_user.id, log_id)
    await db.commit()
    return {"success": True, "message": "Đã xóa bản ghi", "data": None}


@router.delete(
    "",
    summary="Xóa lịch sử hoạt động",
    description=(
        "Truyền ids để xóa các bản ghi cụ thể. "
        "Để body rỗng {} để xóa toàn bộ lịch sử."
    ),
)
async def delete_many(
    body: Optional[DeleteManyRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    if body and body.ids:
        for log_id in body.ids:
            await svc.delete_one(current_user.id, log_id)
        n = len(body.ids)
    else:
        n = await svc.delete_all(current_user.id)
    await db.commit()
    return {"success": True, "message": f"Đã xóa {n} bản ghi", "data": {"deleted": n}}
