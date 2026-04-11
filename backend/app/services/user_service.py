from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from itertools import combinations
from math import ceil
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.drug import DrugInteraction
from app.models.health_profile import HealthProfile
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.user import User
from app.schemas.user import (
    BulkDeleteRequest,
    ChangePasswordRequest,
    HealthProfileCreate,
    HealthProfileListItem,
    HealthProfileResponse,
    HealthProfileUpdate,
    PaginatedResponse,
    PaginationMeta,
    PrescriptionCreate,
    PrescriptionListItem,
    PrescriptionResponse,
    PrescriptionUpdate,
    UpdateProfileRequest,
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_EXT_MAP = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB
_AVATARS_DIR = Path("static/avatars")


# ══════════════════════════════════════════════════════════════════════════════
#  UserService
# ══════════════════════════════════════════════════════════════════════════════

class UserService:
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        email_service: EmailService | None = None,
    ):
        self.db = db
        self.redis = redis
        self.email_service = email_service

    # ── Profile ────────────────────────────────────────────────────────── #

    async def get_profile(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tìm thấy")
        return user

    async def update_profile(self, user_id: int, data: UpdateProfileRequest) -> User:
        user = await self.get_profile(user_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        logger.info(f"Profile updated for user {user_id}")
        return user

    async def change_password(
        self,
        user_id: int,
        data: ChangePasswordRequest,
        background_tasks: BackgroundTasks,
    ) -> None:
        user = await self.get_profile(user_id)

        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản này đăng nhập bằng Google, không có mật khẩu để thay đổi",
            )
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng",
            )

        user.password_hash = hash_password(data.new_password)
        await self.redis.delete(f"refresh:{user_id}")  # Đăng xuất tất cả thiết bị

        if self.email_service:
            changed_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
            await self.email_service.send_password_changed_notification(
                background_tasks, user.email, user.full_name or "", changed_at
            )
        logger.info(f"Password changed for user {user_id}")

    async def upload_avatar(self, user_id: int, file: UploadFile) -> str:
        if file.content_type not in _ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chỉ chấp nhận file ảnh JPEG, PNG hoặc WebP",
            )

        content = await file.read()
        if len(content) > _MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kích thước file không được vượt quá 2MB",
            )

        user = await self.get_profile(user_id)

        # Xóa avatar cũ nếu là file local
        if user.avatar_url and user.avatar_url.startswith("/static/avatars/"):
            old_path = Path(user.avatar_url.lstrip("/"))
            if old_path.exists():
                old_path.unlink(missing_ok=True)

        # Lưu file mới
        _AVATARS_DIR.mkdir(parents=True, exist_ok=True)
        ext = _EXT_MAP[file.content_type]
        filename = f"{user_id}_{int(time.time())}.{ext}"
        filepath = _AVATARS_DIR / filename

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        url = f"/static/avatars/{filename}"
        user.avatar_url = url
        logger.info(f"Avatar uploaded for user {user_id}: {url}")
        return url


# ══════════════════════════════════════════════════════════════════════════════
#  PrescriptionService
# ══════════════════════════════════════════════════════════════════════════════

class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Helpers ────────────────────────────────────────────────────────── #

    async def _get_and_verify(self, user_id: int, prescription_id: int) -> Prescription:
        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.id == prescription_id)
            .options(selectinload(Prescription.items))
        )
        p = result.scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn thuốc không tìm thấy")
        if p.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập đơn thuốc này")
        return p

    # ── CRUD ───────────────────────────────────────────────────────────── #

    async def get_list(
        self,
        user_id: int,
        page: int,
        size: int,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> PaginatedResponse:
        stmt = select(Prescription).where(Prescription.user_id == user_id)

        if search:
            stmt = stmt.where(Prescription.name.ilike(f"%{search}%"))
        if status_filter:
            stmt = stmt.where(Prescription.status == status_filter)

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))

        stmt = (
            stmt
            .options(selectinload(Prescription.items))
            .order_by(Prescription.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        prescriptions = result.scalars().all()

        items = [
            PrescriptionListItem(
                id=p.id,
                name=p.name,
                status=p.status,
                drug_count=len(p.items),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in prescriptions
        ]

        return PaginatedResponse(
            items=items,
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )

    async def get_by_id(self, user_id: int, prescription_id: int) -> Prescription:
        return await self._get_and_verify(user_id, prescription_id)

    async def create(self, user_id: int, data: PrescriptionCreate) -> Prescription:
        prescription = Prescription(
            user_id=user_id,
            name=data.name,
            notes=data.notes,
            status=data.status or PrescriptionStatus.active,
        )
        self.db.add(prescription)
        await self.db.flush()  # Lấy prescription.id

        for item_data in data.items:
            item = PrescriptionItem(
                prescription_id=prescription.id,
                **item_data.model_dump(),
            )
            self.db.add(item)

        await self.db.flush()
        # Reload với items
        await self.db.refresh(prescription)
        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.id == prescription.id)
            .options(selectinload(Prescription.items))
        )
        logger.info(f"Prescription {prescription.id} created for user {user_id}")
        return result.scalar_one()

    async def update(
        self,
        user_id: int,
        prescription_id: int,
        data: PrescriptionUpdate,
    ) -> Prescription:
        prescription = await self._get_and_verify(user_id, prescription_id)

        for field, value in data.model_dump(exclude_none=True, exclude={"items"}).items():
            setattr(prescription, field, value)

        if data.items is not None:
            # Xóa items cũ, tạo lại items mới
            for old_item in list(prescription.items):
                await self.db.delete(old_item)
            await self.db.flush()

            for item_data in data.items:
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    **item_data.model_dump(),
                )
                self.db.add(item)
            await self.db.flush()

        # Reload
        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.id == prescription_id)
            .options(selectinload(Prescription.items))
        )
        logger.info(f"Prescription {prescription_id} updated for user {user_id}")
        return result.scalar_one()

    async def delete(self, user_id: int, prescription_id: int) -> None:
        prescription = await self._get_and_verify(user_id, prescription_id)
        if prescription.status == PrescriptionStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa đơn thuốc đang sử dụng. Vui lòng hoàn thành đơn thuốc trước.",
            )
        await self.db.delete(prescription)
        logger.info(f"Prescription {prescription_id} deleted by user {user_id}")

    async def delete_many(self, user_id: int, ids: list[int]) -> dict:
        deleted, failed = [], []
        for pid in ids:
            try:
                await self.delete(user_id, pid)
                deleted.append(pid)
            except HTTPException:
                failed.append(pid)
        return {"deleted": deleted, "failed": failed}

    async def check_interactions(self, user_id: int, prescription_id: int) -> dict:
        prescription = await self._get_and_verify(user_id, prescription_id)
        drug_ids = list({item.drug_id for item in prescription.items if item.drug_id})

        if len(drug_ids) < 2:
            return {
                "interactions": [],
                "message": "Cần ít nhất 2 thuốc có mã drug_id để kiểm tra tương tác",
            }

        pairs = [
            (min(a, b), max(a, b))
            for a, b in combinations(drug_ids, 2)
        ]

        conditions = [
            and_(DrugInteraction.drug_id_1 == d1, DrugInteraction.drug_id_2 == d2)
            for d1, d2 in pairs
        ]
        result = await self.db.execute(
            select(DrugInteraction).where(or_(*conditions))
        )
        interactions = result.scalars().all()

        return {
            "prescription_id": prescription_id,
            "drugs_checked": drug_ids,
            "interaction_count": len(interactions),
            "interactions": [
                {
                    "drug_1": i.drug_id_1,
                    "drug_2": i.drug_id_2,
                    "severity": i.severity,
                    "type": i.interaction_type,
                    "description": i.description,
                    "recommendation": i.recommendation,
                }
                for i in interactions
            ],
        }


# ══════════════════════════════════════════════════════════════════════════════
#  HealthProfileService
# ══════════════════════════════════════════════════════════════════════════════

class HealthProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Helpers ────────────────────────────────────────────────────────── #

    async def _get_and_verify(self, user_id: int, profile_id: int) -> HealthProfile:
        result = await self.db.execute(
            select(HealthProfile)
            .where(HealthProfile.id == profile_id)
            .options(selectinload(HealthProfile.prescription))
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hồ sơ sức khỏe không tìm thấy")
        if profile.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập hồ sơ này")
        return profile

    async def _verify_prescription_ownership(self, user_id: int, prescription_id: int) -> None:
        result = await self.db.execute(
            select(Prescription).where(
                Prescription.id == prescription_id,
                Prescription.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Đơn thuốc không tìm thấy hoặc không thuộc về bạn",
            )

    # ── CRUD ───────────────────────────────────────────────────────────── #

    async def get_list(
        self,
        user_id: int,
        page: int,
        size: int,
        search: Optional[str] = None,
        exam_date_from: Optional[date] = None,
        exam_date_to: Optional[date] = None,
    ) -> PaginatedResponse:
        from datetime import date

        stmt = select(HealthProfile).where(HealthProfile.user_id == user_id)

        if search:
            stmt = stmt.where(HealthProfile.diagnosis_name.ilike(f"%{search}%"))
        if exam_date_from:
            stmt = stmt.where(HealthProfile.exam_date >= exam_date_from)
        if exam_date_to:
            stmt = stmt.where(HealthProfile.exam_date <= exam_date_to)

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))

        stmt = stmt.order_by(HealthProfile.exam_date.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        profiles = result.scalars().all()

        return PaginatedResponse(
            items=[HealthProfileListItem.model_validate(p) for p in profiles],
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )

    async def get_by_id(self, user_id: int, profile_id: int) -> HealthProfile:
        return await self._get_and_verify(user_id, profile_id)

    async def create(self, user_id: int, data: HealthProfileCreate) -> HealthProfile:
        if data.prescription_id:
            await self._verify_prescription_ownership(user_id, data.prescription_id)

        profile = HealthProfile(user_id=user_id, **data.model_dump())
        self.db.add(profile)
        await self.db.flush()

        # Reload với relationship
        result = await self.db.execute(
            select(HealthProfile)
            .where(HealthProfile.id == profile.id)
            .options(selectinload(HealthProfile.prescription))
        )
        logger.info(f"HealthProfile {profile.id} created for user {user_id}")
        return result.scalar_one()

    async def update(
        self,
        user_id: int,
        profile_id: int,
        data: HealthProfileUpdate,
    ) -> HealthProfile:
        profile = await self._get_and_verify(user_id, profile_id)

        update_data = data.model_dump(exclude_none=True)
        if "prescription_id" in update_data and update_data["prescription_id"]:
            await self._verify_prescription_ownership(user_id, update_data["prescription_id"])

        for field, value in update_data.items():
            setattr(profile, field, value)

        await self.db.flush()

        # Reload with relationship to avoid MissingGreenlet during serialization
        result = await self.db.execute(
            select(HealthProfile)
            .where(HealthProfile.id == profile_id)
            .options(selectinload(HealthProfile.prescription))
        )
        logger.info(f"HealthProfile {profile_id} updated for user {user_id}")
        return result.scalar_one()

    async def delete(self, user_id: int, profile_id: int) -> None:
        profile = await self._get_and_verify(user_id, profile_id)
        await self.db.delete(profile)
        logger.info(f"HealthProfile {profile_id} deleted by user {user_id}")

    async def delete_many(self, user_id: int, ids: list[int]) -> dict:
        deleted, failed = [], []
        for pid in ids:
            try:
                await self.delete(user_id, pid)
                deleted.append(pid)
            except HTTPException:
                failed.append(pid)
        return {"deleted": deleted, "failed": failed}
