from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.deps import get_current_user, get_optional_user
from app.database import get_db
from app.redis_client import get_redis
from app.models.log import ActivityLog
from app.models.user import User
from app.schemas.drug import (
    DrugDetailResponse,
    DrugListItem,
    InteractionCheckRequest,
    InteractionCheckResult,
)
from app.services.drug_service import DrugService, InteractionService

# ── Drug router ────────────────────────────────────────────────────────────

drug_router = APIRouter(prefix="/drugs", tags=["💊 Thuốc"])

# ── Interaction router ─────────────────────────────────────────────────────

interaction_router = APIRouter(prefix="/interactions", tags=["⚠️ Tương tác thuốc"])


# ── Helpers ────────────────────────────────────────────────────────────────

def _drug_svc(db: AsyncSession, redis: Redis) -> DrugService:
    return DrugService(db, redis)


def _interaction_svc(db: AsyncSession, redis: Redis) -> InteractionService:
    return InteractionService(db, redis)


async def _log(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    detail: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    """Add an ActivityLog entry to the current session (committed by get_db)."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log)


# ══════════════════════════════════════════════════════════════════════════════
#  Drug routes
# ══════════════════════════════════════════════════════════════════════════════

@drug_router.get(
    "",
    summary="Danh sách thuốc",
    description="Tìm kiếm theo tên, mã DB hoặc mã ATC. Public — không cần đăng nhập.",
)
async def list_drugs(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã DB"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _drug_svc(db, redis)
    result = await svc.get_list(page, size, search)

    if current_user and search:
        await _log(db, current_user.id, "DRUG_SEARCH",
                   detail={"query": search}, request=request)
    return result


@drug_router.get(
    "/{drug_id}",
    response_model=DrugDetailResponse,
    summary="Chi tiết thuốc",
)
async def get_drug(
    drug_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _drug_svc(db, redis)
    drug = await svc.get_by_id(drug_id)

    if current_user:
        await _log(db, current_user.id, "DRUG_SEARCH",
                   entity_type="drug", entity_id=drug_id, request=request)
    return drug


@drug_router.get(
    "/{drug_id}/interactions",
    summary="Tương tác của một thuốc",
    description="Liệt kê tất cả cặp tương tác liên quan đến thuốc này.",
)
async def get_drug_interactions(
    drug_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _drug_svc(db, redis)
    return await svc.get_drug_interactions(drug_id, page, size)


# ══════════════════════════════════════════════════════════════════════════════
#  Interaction routes
# ══════════════════════════════════════════════════════════════════════════════

@interaction_router.post(
    "/check",
    response_model=InteractionCheckResult,
    summary="Kiểm tra tương tác thuốc",
    description="Kiểm tra tất cả cặp tương tác trong danh sách thuốc. Yêu cầu đăng nhập.",
)
async def check_interactions(
    data: InteractionCheckRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _interaction_svc(db, redis)
    result = await svc.check_interactions(data.drug_ids)

    await _log(
        db, current_user.id, "INTERACTION_CHECK",
        detail={
            "drug_ids": data.drug_ids,
            "has_interaction": result.has_interaction,
            "interaction_count": len(result.interactions),
        },
        request=request,
    )
    return result


@interaction_router.post(
    "/check/export",
    summary="Xuất kết quả tương tác ra file Excel",
    description="Kiểm tra tương tác và tải về file .xlsx. Yêu cầu đăng nhập.",
)
async def export_interactions(
    data: InteractionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _interaction_svc(db, redis)
    content = await svc.export_result(data.drug_ids)

    filename = f"tuong-tac-thuoc-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
