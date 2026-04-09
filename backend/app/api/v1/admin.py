from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user
from app.database import get_db
from app.models.user import User
from app.redis_client import get_redis
from app.schemas.admin import (
    AdminDrugCreate,
    AdminDrugUpdate,
    AdminInteractionCreate,
    AdminInteractionUpdate,
    AdminProductCreate,
    AdminProductUpdate,
    AdminUpdateUser,
    AdminUserDetail,
    AdminUserListItem,
    AdminWarningCreate,
)
from app.schemas.drug import DrugDetailResponse, DrugInteractionResponse, DrugProductResponse, DrugWarningResponse
from app.schemas.user import PaginatedResponse, UserResponse
from app.services.admin_service import AdminDrugService, AdminInteractionService, AdminUserService
from app.services.log_service import ActivityLogService, SystemLogService

router = APIRouter(prefix="/admin", tags=["🔧 Admin"])


# ── Helpers ────────────────────────────────────────────────────────────────

async def _sys_log(db, admin_id: int, action: str, entity: str, entity_id) -> None:
    try:
        await SystemLogService(db).log(
            level="INFO",
            source="admin_api",
            message=f"Admin #{admin_id} {action} {entity} #{entity_id}",
            detail={"admin_id": admin_id, "entity": entity, "entity_id": str(entity_id)},
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  UC08: User Management
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/users",
    response_model=PaginatedResponse,
    summary="Danh sách người dùng",
)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminUserService(db).get_list(page, size, search, role, is_active)


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Chi tiết người dùng",
)
async def get_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminUserService(db).get_by_id(user_id)


@router.put(
    "/users/{user_id}",
    summary="Cập nhật thông tin người dùng",
)
async def update_user(
    user_id: int,
    data: AdminUpdateUser,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await AdminUserService(db).update(user_id, data, admin.id)
    await _sys_log(db, admin.id, "updated", "user", user_id)
    await db.commit()
    return {"success": True, "message": "Cập nhật thành công", "data": UserResponse.model_validate(user).model_dump()}


@router.patch(
    "/users/{user_id}/toggle-active",
    summary="Kích hoạt / Vô hiệu hóa tài khoản",
)
async def toggle_active(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await AdminUserService(db).toggle_active(user_id, admin.id)
    msg = "Kích hoạt thành công" if user.is_active else "Vô hiệu hóa thành công"
    await _sys_log(db, admin.id, "toggle_active", "user", user_id)
    await db.commit()
    return {"success": True, "message": msg, "data": {"user_id": user_id, "is_active": user.is_active}}


# ══════════════════════════════════════════════════════════════════════════════
#  UC09: Drug Management
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/drugs",
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thuốc mới",
)
async def create_drug(
    data: AdminDrugCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.drug import Drug

    drug = await AdminDrugService(db, redis).create(data)
    await _sys_log(db, admin.id, "created", "drug", drug.id)
    await db.commit()
    # Reload with relationships
    await db.refresh(drug)
    return {
        "success": True,
        "message": "Thêm thuốc thành công",
        "data": DrugDetailResponse.model_validate(drug).model_dump(),
    }


@router.put(
    "/drugs/{drug_id}",
    summary="Cập nhật thông tin thuốc",
)
async def update_drug(
    drug_id: str,
    data: AdminDrugUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    drug = await AdminDrugService(db, redis).update(drug_id, data)
    await _sys_log(db, admin.id, "updated", "drug", drug_id)
    await db.commit()
    await db.refresh(drug)
    return {
        "success": True,
        "message": "Cập nhật thành công",
        "data": DrugDetailResponse.model_validate(drug).model_dump(),
    }


@router.delete(
    "/drugs/{drug_id}",
    summary="Xóa thuốc",
)
async def delete_drug(
    drug_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await AdminDrugService(db, redis).delete(drug_id)
    await _sys_log(db, admin.id, "deleted", "drug", drug_id)
    await db.commit()
    return {"success": True, "message": "Đã xóa thuốc", "data": None}


@router.post(
    "/drugs/{drug_id}/products",
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thông tin sản phẩm",
)
async def add_product(
    drug_id: str,
    data: AdminProductCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    product = await AdminDrugService(db, redis).add_product(drug_id, data)
    await _sys_log(db, admin.id, "created", "product", product.id)
    await db.commit()
    return {"success": True, "data": DrugProductResponse.model_validate(product).model_dump()}


@router.put(
    "/drugs/{drug_id}/products/{product_id}",
    summary="Cập nhật thông tin sản phẩm",
)
async def update_product(
    drug_id: str,
    product_id: int,
    data: AdminProductUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    product = await AdminDrugService(db, redis).update_product(drug_id, product_id, data)
    await _sys_log(db, admin.id, "updated", "product", product_id)
    await db.commit()
    return {"success": True, "data": DrugProductResponse.model_validate(product).model_dump()}


@router.delete(
    "/drugs/{drug_id}/products/{product_id}",
    summary="Xóa thông tin sản phẩm",
)
async def delete_product(
    drug_id: str,
    product_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await AdminDrugService(db, redis).delete_product(drug_id, product_id)
    await _sys_log(db, admin.id, "deleted", "product", product_id)
    await db.commit()
    return {"success": True, "message": "Đã xóa thông tin sản phẩm", "data": None}


@router.post(
    "/drugs/{drug_id}/warnings",
    status_code=status.HTTP_201_CREATED,
    summary="Thêm cảnh báo thuốc",
)
async def add_warning(
    drug_id: str,
    data: AdminWarningCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    warning = await AdminDrugService(db, redis).add_warning(drug_id, data.warning_text)
    await _sys_log(db, admin.id, "created", "warning", warning.id)
    await db.commit()
    return {"success": True, "data": DrugWarningResponse.model_validate(warning).model_dump()}


@router.delete(
    "/drugs/{drug_id}/warnings/{warning_id}",
    summary="Xóa cảnh báo thuốc",
)
async def delete_warning(
    drug_id: str,
    warning_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await AdminDrugService(db, redis).delete_warning(drug_id, warning_id)
    await _sys_log(db, admin.id, "deleted", "warning", warning_id)
    await db.commit()
    return {"success": True, "message": "Đã xóa cảnh báo", "data": None}


# ══════════════════════════════════════════════════════════════════════════════
#  UC10: Interaction Management
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/interactions",
    response_model=PaginatedResponse,
    summary="Danh sách tương tác thuốc",
)
async def list_interactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    drug_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    return await AdminInteractionService(db, redis).get_list(page, size, drug_id, severity)


@router.post(
    "/interactions",
    status_code=status.HTTP_201_CREATED,
    summary="Thêm tương tác thuốc mới",
)
async def create_interaction(
    data: AdminInteractionCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    interaction = await AdminInteractionService(db, redis).create(data)
    await _sys_log(db, admin.id, "created", "interaction", interaction.id)
    await db.commit()
    return {
        "success": True,
        "data": DrugInteractionResponse(
            id=interaction.id,
            drug_id_1=interaction.drug_id_1,
            drug_id_2=interaction.drug_id_2,
            interaction_type=interaction.interaction_type,
            severity=interaction.severity,
            description=interaction.description,
            recommendation=interaction.recommendation,
        ).model_dump(),
    }


@router.put(
    "/interactions/{interaction_id}",
    summary="Cập nhật tương tác thuốc",
)
async def update_interaction(
    interaction_id: int,
    data: AdminInteractionUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    interaction = await AdminInteractionService(db, redis).update(interaction_id, data)
    await _sys_log(db, admin.id, "updated", "interaction", interaction_id)
    await db.commit()
    return {
        "success": True,
        "data": DrugInteractionResponse(
            id=interaction.id,
            drug_id_1=interaction.drug_id_1,
            drug_id_2=interaction.drug_id_2,
            interaction_type=interaction.interaction_type,
            severity=interaction.severity,
            description=interaction.description,
            recommendation=interaction.recommendation,
        ).model_dump(),
    }


@router.delete(
    "/interactions/{interaction_id}",
    summary="Xóa tương tác thuốc",
)
async def delete_interaction(
    interaction_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    await AdminInteractionService(db, redis).delete(interaction_id)
    await _sys_log(db, admin.id, "deleted", "interaction", interaction_id)
    await db.commit()
    return {"success": True, "message": "Đã xóa tương tác thuốc", "data": None}


# ══════════════════════════════════════════════════════════════════════════════
#  UC11: Logs & Stats
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/logs/system",
    response_model=PaginatedResponse,
    summary="System logs",
)
async def get_system_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SystemLogService(db).get_list(page, size, level, source, date_from, date_to)


@router.get(
    "/logs/system/export",
    summary="Xuất system logs ra Excel",
)
async def export_system_logs(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    content = await SystemLogService(db).export_xlsx()
    filename = f"system-logs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/logs/activity",
    response_model=PaginatedResponse,
    summary="Lịch sử hoạt động tất cả users",
    description=(
        "Admin xem được activity của tất cả users. "
        "Lọc theo user_id để xem của user cụ thể."
    ),
)
async def get_activity_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await ActivityLogService(db).get_all_history(
        page, size, user_id, action, date_from, date_to
    )


@router.get(
    "/logs/activity/export",
    summary="Xuất activity logs ra Excel",
)
async def export_activity_logs(
    user_id: Optional[int] = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    content = await ActivityLogService(db).export_xlsx(user_id=user_id)
    filename = f"activity-logs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/stats",
    summary="Thống kê tổng quan hệ thống",
)
async def get_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stats = await AdminUserService(db).get_stats()
    return {"success": True, "message": "Thành công", "data": stats.model_dump()}
