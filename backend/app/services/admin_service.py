from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import List, Optional

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drug import Drug, DrugInteraction, DrugBrandName, DrugWarning
from app.models.log import ActivityLog
from app.models.chat_message import ChatMessage
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.models.health_profile import HealthProfile
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminDrugCreate,
    AdminDrugUpdate,
    AdminInteractionCreate,
    AdminInteractionUpdate,
    AdminBrandNameCreate,
    AdminBrandNameUpdate,
    AdminStatsResponse,
    AdminUpdateUser,
    AdminUserDetail,
    AdminUserListItem,
)
from app.schemas.drug import DrugInteractionResponse
from app.schemas.user import PaginatedResponse, PaginationMeta

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  AdminUserService
# ══════════════════════════════════════════════════════════════════════════════

class AdminUserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_list(
        self,
        page: int,
        size: int,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse:
        stmt = select(User)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.username.ilike(term),
                    User.email.ilike(term),
                    User.full_name.ilike(term),
                )
            )
        if role:
            stmt = stmt.where(User.role == UserRole(role))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        total = await self.db.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        rows = (
            await self.db.execute(
                stmt.order_by(User.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()

        return PaginatedResponse(
            items=[AdminUserListItem.model_validate(u) for u in rows],
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )

    async def get_by_id(self, user_id: int) -> AdminUserDetail:
        user = await self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

        pres_count = await self.db.scalar(
            select(func.count()).where(Prescription.user_id == user_id)
        )
        hp_count = await self.db.scalar(
            select(func.count()).where(HealthProfile.user_id == user_id)
        )
        log_count = await self.db.scalar(
            select(func.count()).where(ActivityLog.user_id == user_id)
        )

        detail = AdminUserDetail.model_validate(user)
        detail.prescription_count = pres_count or 0
        detail.health_profile_count = hp_count or 0
        detail.activity_log_count = log_count or 0
        return detail

    async def update(self, user_id: int, data: AdminUpdateUser, admin_id: int) -> User:
        user = await self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

        if data.role == "user" and user_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tự hạ quyền Admin của chính mình",
            )

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone is not None:
            user.phone = data.phone
        if data.role is not None:
            user.role = UserRole(data.role)
        if data.is_active is not None:
            user.is_active = data.is_active

        await self.db.flush()
        return user

    async def toggle_active(self, user_id: int, admin_id: int) -> User:
        user = await self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

        if user_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể tự vô hiệu hóa tài khoản Admin của chính mình",
            )

        user.is_active = not user.is_active
        await self.db.flush()
        return user

    async def get_stats(self) -> AdminStatsResponse:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        (
            total_users,
            active_users,
            total_drugs,
            total_interactions,
            total_prescriptions,
            active_prescriptions,
            total_chat_messages,
            new_users_today,
            new_users_this_week,
        ) = await asyncio.gather(
            self.db.scalar(select(func.count(User.id))),
            self.db.scalar(select(func.count(User.id)).where(User.is_active == True)),
            self.db.scalar(select(func.count(Drug.id))),
            self.db.scalar(select(func.count(DrugInteraction.drug_id))),
            self.db.scalar(select(func.count(Prescription.id))),
            self.db.scalar(
                select(func.count(Prescription.id)).where(Prescription.status == PrescriptionStatus.active)
            ),
            self.db.scalar(select(func.count(ChatMessage.id))),
            self.db.scalar(
                select(func.count(User.id)).where(User.created_at >= today_start)
            ),
            self.db.scalar(
                select(func.count(User.id)).where(User.created_at >= week_start)
            ),
        )

        return AdminStatsResponse(
            total_users=total_users or 0,
            active_users=active_users or 0,
            total_drugs=total_drugs or 0,
            total_interactions=total_interactions or 0,
            total_prescriptions=total_prescriptions or 0,
            active_prescriptions=active_prescriptions or 0,
            new_users_today=new_users_today or 0,
            new_users_this_week=new_users_this_week or 0,
            total_chat_messages=total_chat_messages or 0,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  AdminDrugService
# ══════════════════════════════════════════════════════════════════════════════

class AdminDrugService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def _invalidate_cache(self, drug_id: Optional[str] = None) -> None:
        if drug_id:
            await self.redis.delete(f"cache:drug:{drug_id}")
        async for key in self.redis.scan_iter("cache:drugs:list:*"):
            await self.redis.delete(key)

    async def create(self, data: AdminDrugCreate) -> Drug:
        if data.id is None:
            while True:
                count = await self.db.scalar(select(func.count(Drug.id)))
                new_id = f"DB{(count or 0) + 1:06d}"
                existing = await self.db.scalar(select(Drug).where(Drug.id == new_id))
                if not existing:
                    break
        else:
            new_id = data.id
            existing = await self.db.scalar(select(Drug).where(Drug.id == new_id))
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Mã thuốc '{new_id}' đã tồn tại",
                )

        drug = Drug(
            id=new_id,
            generic_name=data.generic_name,
            description=data.description,
            chemical_formula=data.chemical_formula,
            molecular_formula=data.molecular_formula,
        )
        self.db.add(drug)
        await self.db.flush()
        await self._invalidate_cache()
        return drug

    async def update(self, drug_id: str, data: AdminDrugUpdate) -> Drug:
        drug = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        if not drug:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thuốc '{drug_id}' không tìm thấy")

        if data.generic_name is not None:
            drug.generic_name = data.generic_name
        if data.description is not None:
            drug.description = data.description
        if data.chemical_formula is not None:
            drug.chemical_formula = data.chemical_formula
        if data.molecular_formula is not None:
            drug.molecular_formula = data.molecular_formula

        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return drug

    async def delete(self, drug_id: str) -> None:
        drug = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        if not drug:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thuốc '{drug_id}' không tìm thấy")

        active_use = await self.db.scalar(
            select(func.count(PrescriptionItem.id))
            .join(Prescription, PrescriptionItem.prescription_id == Prescription.id)
            .where(
                PrescriptionItem.drug_id == drug_id,
                Prescription.status == PrescriptionStatus.active,
            )
        )
        if active_use:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Không thể xóa thuốc đang được dùng trong đơn thuốc active. "
                    "Vui lòng hoàn thành các đơn thuốc liên quan trước."
                ),
            )

        await self.db.delete(drug)
        await self.db.flush()
        await self._invalidate_cache(drug_id)

    # ── Brand Names ───────────────────────────────────────────────────────

    async def _get_drug_or_404(self, drug_id: str) -> Drug:
        drug = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        if not drug:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thuốc '{drug_id}' không tìm thấy")
        return drug

    async def _get_brand_name_or_404(self, drug_id: str, brand_id: int) -> DrugBrandName:
        brand = await self.db.scalar(
            select(DrugBrandName).where(
                DrugBrandName.id == brand_id, DrugBrandName.drug_id == drug_id
            )
        )
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sản phẩm thương mại không tìm thấy")
        return brand

    async def add_brand_name(self, drug_id: str, data: AdminBrandNameCreate) -> DrugBrandName:
        await self._get_drug_or_404(drug_id)
        brand = DrugBrandName(
            drug_id=drug_id,
            name=data.name,
            route=data.route,
            strength=data.strength,
            dosage_form=data.dosage_form,
            country=data.country,
            image_url=data.image_url,
        )
        self.db.add(brand)
        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return brand

    async def update_brand_name(
        self, drug_id: str, brand_id: int, data: AdminBrandNameUpdate
    ) -> DrugBrandName:
        brand = await self._get_brand_name_or_404(drug_id, brand_id)
        if data.name is not None:
            brand.name = data.name
        if data.route is not None:
            brand.route = data.route
        if data.strength is not None:
            brand.strength = data.strength
        if data.dosage_form is not None:
            brand.dosage_form = data.dosage_form
        if data.country is not None:
            brand.country = data.country
        if data.image_url is not None:
            brand.image_url = data.image_url
        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return brand

    async def delete_brand_name(self, drug_id: str, brand_id: int) -> None:
        brand = await self._get_brand_name_or_404(drug_id, brand_id)
        await self.db.delete(brand)
        await self.db.flush()
        await self._invalidate_cache(drug_id)

    # ── Warnings ──────────────────────────────────────────────────────────

    async def add_warning(self, drug_id: str, warning_text: str) -> DrugWarning:
        await self._get_drug_or_404(drug_id)
        warning = DrugWarning(drug_id=drug_id, warning_text=warning_text)
        self.db.add(warning)
        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return warning

    async def delete_warning(self, drug_id: str, warning_id: int) -> None:
        warning = await self.db.scalar(
            select(DrugWarning).where(
                DrugWarning.id == warning_id, DrugWarning.drug_id == drug_id
            )
        )
        if not warning:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cảnh báo không tìm thấy")
        await self.db.delete(warning)
        await self.db.flush()
        await self._invalidate_cache(drug_id)


# ══════════════════════════════════════════════════════════════════════════════
#  AdminInteractionService
# ══════════════════════════════════════════════════════════════════════════════

class AdminInteractionService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def _invalidate_interaction_cache(self, drug_id: str, interacts_with_id: str) -> None:
        await self.redis.delete(f"cache:interaction:{drug_id}:{interacts_with_id}")
        await self.redis.delete(f"cache:interaction:{interacts_with_id}:{drug_id}")

    async def get_list(
        self,
        page: int,
        size: int,
        drug_id: Optional[str] = None,
    ) -> PaginatedResponse:
        stmt = select(DrugInteraction)
        if drug_id:
            stmt = stmt.where(
                or_(
                    DrugInteraction.drug_id == drug_id,
                    DrugInteraction.interacts_with_id == drug_id,
                )
            )

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))

        rows = (
            await self.db.execute(
                stmt.order_by(DrugInteraction.drug_id.asc(), DrugInteraction.interacts_with_id.asc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()

        # Fetch generic names for drug_id column only (interacts_with_id may not be in DB)
        drug_ids_in_rows = {r.drug_id for r in rows}
        drug_names: dict[str, str] = {}
        if drug_ids_in_rows:
            drugs = (await self.db.execute(select(Drug).where(Drug.id.in_(drug_ids_in_rows)))).scalars().all()
            drug_names = {d.id: d.generic_name for d in drugs}

        items = [
            DrugInteractionResponse(
                drug_id=r.drug_id,
                interacts_with_id=r.interacts_with_id,
                interacts_with_name=r.interacts_with_name,
                drug_name=drug_names.get(r.drug_id),
            )
            for r in rows
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

    async def create(self, data: AdminInteractionCreate) -> DrugInteraction:
        # Verify drug_id exists (interacts_with_id may not be in DB)
        exists = await self.db.scalar(select(func.count(Drug.id)).where(Drug.id == data.drug_id))
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thuốc '{data.drug_id}' không tìm thấy",
            )

        # Check duplicate
        existing = await self.db.scalar(
            select(DrugInteraction).where(
                and_(
                    DrugInteraction.drug_id == data.drug_id,
                    DrugInteraction.interacts_with_id == data.interacts_with_id,
                )
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tương tác giữa 2 thuốc này đã tồn tại",
            )

        interaction = DrugInteraction(
            drug_id=data.drug_id,
            interacts_with_id=data.interacts_with_id,
            interacts_with_name=data.interacts_with_name,
        )
        self.db.add(interaction)
        await self.db.flush()
        await self._invalidate_interaction_cache(data.drug_id, data.interacts_with_id)
        return interaction

    async def update(
        self, drug_id: str, interacts_with_id: str, data: AdminInteractionUpdate
    ) -> DrugInteraction:
        interaction = await self.db.scalar(
            select(DrugInteraction).where(
                and_(
                    DrugInteraction.drug_id == drug_id,
                    DrugInteraction.interacts_with_id == interacts_with_id,
                )
            )
        )
        if not interaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tương tác không tìm thấy")

        if data.interacts_with_name is not None:
            interaction.interacts_with_name = data.interacts_with_name

        await self.db.flush()
        await self._invalidate_interaction_cache(drug_id, interacts_with_id)
        return interaction

    async def delete(self, drug_id: str, interacts_with_id: str) -> None:
        interaction = await self.db.scalar(
            select(DrugInteraction).where(
                and_(
                    DrugInteraction.drug_id == drug_id,
                    DrugInteraction.interacts_with_id == interacts_with_id,
                )
            )
        )
        if not interaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tương tác không tìm thấy")

        await self._invalidate_interaction_cache(drug_id, interacts_with_id)
        await self.db.delete(interaction)
        await self.db.flush()
