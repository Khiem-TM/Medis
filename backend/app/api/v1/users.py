from datetime import date
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File,
    Query, UploadFile, status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.deps import get_current_user
from app.database import get_db
from app.redis_client import get_redis
from app.models.user import User
from app.schemas.user import (
    BulkDeleteRequest,
    ChangePasswordRequest,
    HealthProfileCreate,
    HealthProfileListItem,
    HealthProfileResponse,
    HealthProfileUpdate,
    PaginatedResponse,
    PrescriptionCreate,
    PrescriptionListItem,
    PrescriptionResponse,
    PrescriptionUpdate,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.email_service import EmailService
from app.services.user_service import (
    HealthProfileService,
    PrescriptionService,
    UserService,
)

router = APIRouter(prefix="/users", tags=["👤 User Profile"])


# ── Service factories ──────────────────────────────────────────────────────

def _user_svc(db: AsyncSession, redis: Redis) -> UserService:
    return UserService(db, redis, EmailService())

def _prescription_svc(db: AsyncSession) -> PrescriptionService:
    return PrescriptionService(db)

def _health_svc(db: AsyncSession) -> HealthProfileService:
    return HealthProfileService(db)


# ══════════════════════════════════════════════════════════════════════════════
#  Profile
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin cá nhân",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Cập nhật thông tin cá nhân",
)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _user_svc(db, redis)
    user = await svc.update_profile(current_user.id, data)
    await db.commit()
    return user


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Đổi mật khẩu",
)
async def change_password(
    data: ChangePasswordRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _user_svc(db, redis)
    await svc.change_password(current_user.id, data, background_tasks)
    await db.commit()
    return {"message": "Mật khẩu đã được thay đổi thành công. Vui lòng đăng nhập lại."}


@router.post(
    "/me/avatar",
    status_code=status.HTTP_200_OK,
    summary="Upload ảnh đại diện",
    description="Chấp nhận JPEG, PNG, WebP. Tối đa 2MB.",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = _user_svc(db, redis)
    url = await svc.upload_avatar(current_user.id, file)
    await db.commit()
    return {"avatar_url": url}


# ══════════════════════════════════════════════════════════════════════════════
#  Prescriptions
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/me/prescriptions",
    summary="Danh sách đơn thuốc",
    description="Hỗ trợ tìm kiếm theo tên và lọc theo trạng thái.",
)
async def list_prescriptions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Tìm theo tên đơn thuốc"),
    status: Optional[str] = Query(None, description="Lọc: active | completed"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    return await svc.get_list(current_user.id, page, size, search, status)


@router.post(
    "/me/prescriptions",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo đơn thuốc mới",
)
async def create_prescription(
    data: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    result = await svc.create(current_user.id, data)
    await db.commit()
    return result


@router.get(
    "/me/prescriptions/{prescription_id}",
    response_model=PrescriptionResponse,
    summary="Chi tiết đơn thuốc",
)
async def get_prescription(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    return await svc.get_by_id(current_user.id, prescription_id)


@router.put(
    "/me/prescriptions/{prescription_id}",
    response_model=PrescriptionResponse,
    summary="Cập nhật đơn thuốc",
)
async def update_prescription(
    prescription_id: int,
    data: PrescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    result = await svc.update(current_user.id, prescription_id, data)
    await db.commit()
    return result


@router.delete(
    "/me/prescriptions/{prescription_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa đơn thuốc",
    description="Chỉ xóa được đơn có trạng thái 'completed'.",
)
async def delete_prescription(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    await svc.delete(current_user.id, prescription_id)
    await db.commit()
    return {"message": "Đơn thuốc đã được xóa"}


@router.delete(
    "/me/prescriptions",
    status_code=status.HTTP_200_OK,
    summary="Xóa nhiều đơn thuốc",
)
async def delete_many_prescriptions(
    body: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    result = await svc.delete_many(current_user.id, body.ids)
    await db.commit()
    return result


@router.get(
    "/me/prescriptions/{prescription_id}/interactions",
    summary="Kiểm tra tương tác thuốc",
    description="Kiểm tra tương tác giữa các thuốc trong đơn (cần ít nhất 2 thuốc có drug_id).",
)
async def check_interactions(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _prescription_svc(db)
    return await svc.check_interactions(current_user.id, prescription_id)


# ══════════════════════════════════════════════════════════════════════════════
#  Health Profiles
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/me/health-profiles",
    summary="Danh sách hồ sơ sức khỏe",
)
async def list_health_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Tìm theo tên bệnh / chẩn đoán"),
    exam_date_from: Optional[date] = Query(None, description="Lọc từ ngày khám"),
    exam_date_to: Optional[date] = Query(None, description="Lọc đến ngày khám"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _health_svc(db)
    return await svc.get_list(current_user.id, page, size, search, exam_date_from, exam_date_to)


@router.post(
    "/me/health-profiles",
    response_model=HealthProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo hồ sơ sức khỏe mới",
)
async def create_health_profile(
    data: HealthProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _health_svc(db)
    result = await svc.create(current_user.id, data)
    await db.commit()
    return result


@router.get(
    "/me/health-profiles/{profile_id}",
    response_model=HealthProfileResponse,
    summary="Chi tiết hồ sơ sức khỏe",
)
async def get_health_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _health_svc(db)
    return await svc.get_by_id(current_user.id, profile_id)


@router.put(
    "/me/health-profiles/{profile_id}",
    response_model=HealthProfileResponse,
    summary="Cập nhật hồ sơ sức khỏe",
)
async def update_health_profile(
    profile_id: int,
    data: HealthProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _health_svc(db)
    result = await svc.update(current_user.id, profile_id, data)
    await db.commit()
    return result


@router.delete(
    "/me/health-profiles/{profile_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa hồ sơ sức khỏe",
)
async def delete_health_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _health_svc(db)
    await svc.delete(current_user.id, profile_id)
    await db.commit()
    return {"message": "Hồ sơ sức khỏe đã được xóa"}


@router.delete(
    "/me/health-profiles",
    status_code=status.HTTP_200_OK,
    summary="Xóa nhiều hồ sơ sức khỏe",
)
async def delete_many_health_profiles(
    body: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _health_svc(db)
    result = await svc.delete_many(current_user.id, body.ids)
    await db.commit()
    return result
