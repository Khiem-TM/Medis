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

from app.models.drug import Drug, DrugInteraction, DrugProduct, DrugWarning, InteractionSeverity
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
    AdminProductCreate,
    AdminProductUpdate,
    AdminStatsResponse,
    AdminUpdateUser,
    AdminUserDetail,
    AdminUserListItem,
)
from app.schemas.drug import DrugDetailResponse, DrugInteractionResponse, DrugProductResponse, DrugWarningResponse
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
            self.db.scalar(select(func.count(DrugInteraction.id))),
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
        from datetime import datetime, timezone

        if data.id is None:
            # Auto-generate unique DB-style id
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
            name=data.name,
            atc_code=data.atc_code,
            dosage_form=data.dosage_form,
            description=data.description,
            classification=data.classification,
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(drug)
        await self.db.flush()
        await self._invalidate_cache()
        return drug

    async def update(self, drug_id: str, data: AdminDrugUpdate) -> Drug:
        drug = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        if not drug:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thuốc '{drug_id}' không tìm thấy")

        if data.name is not None:
            drug.name = data.name
        if data.atc_code is not None:
            drug.atc_code = data.atc_code
        if data.dosage_form is not None:
            drug.dosage_form = data.dosage_form
        if data.description is not None:
            drug.description = data.description
        if data.classification is not None:
            drug.classification = data.classification

        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return drug

    async def delete(self, drug_id: str) -> None:
        drug = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        if not drug:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thuốc '{drug_id}' không tìm thấy")

        # Check if used in active prescriptions
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

    # ── Products ──────────────────────────────────────────────────────────

    async def _get_drug_or_404(self, drug_id: str) -> Drug:
        drug = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        if not drug:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thuốc '{drug_id}' không tìm thấy")
        return drug

    async def _get_product_or_404(self, drug_id: str, product_id: int) -> DrugProduct:
        product = await self.db.scalar(
            select(DrugProduct).where(
                DrugProduct.id == product_id, DrugProduct.drug_id == drug_id
            )
        )
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thông tin sản phẩm không tìm thấy")
        return product

    async def add_product(self, drug_id: str, data: AdminProductCreate) -> DrugProduct:
        await self._get_drug_or_404(drug_id)
        product = DrugProduct(
            drug_id=drug_id,
            trade_name=data.trade_name,
            route=data.route,
            dosage=data.dosage,
            formulation=data.formulation,
            origin=data.origin,
        )
        self.db.add(product)
        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return product

    async def update_product(
        self, drug_id: str, product_id: int, data: AdminProductUpdate
    ) -> DrugProduct:
        product = await self._get_product_or_404(drug_id, product_id)
        if data.trade_name is not None:
            product.trade_name = data.trade_name
        if data.route is not None:
            product.route = data.route
        if data.dosage is not None:
            product.dosage = data.dosage
        if data.formulation is not None:
            product.formulation = data.formulation
        if data.origin is not None:
            product.origin = data.origin
        await self.db.flush()
        await self._invalidate_cache(drug_id)
        return product

    async def delete_product(self, drug_id: str, product_id: int) -> None:
        product = await self._get_product_or_404(drug_id, product_id)
        await self.db.delete(product)
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

    async def _invalidate_interaction_cache(self, drug_id_1: str, drug_id_2: str) -> None:
        a, b = sorted([drug_id_1, drug_id_2])
        await self.redis.delete(f"cache:interaction:{a}:{b}")

    async def get_list(
        self,
        page: int,
        size: int,
        drug_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> PaginatedResponse:
        stmt = select(DrugInteraction)
        if drug_id:
            stmt = stmt.where(
                or_(
                    DrugInteraction.drug_id_1 == drug_id,
                    DrugInteraction.drug_id_2 == drug_id,
                )
            )
        if severity:
            stmt = stmt.where(DrugInteraction.severity == InteractionSeverity(severity))

        total = await self.db.scalar(
            select(func.count()).select_from(stmt.subquery())
        )

        rows = (
            await self.db.execute(
                stmt.order_by(DrugInteraction.id.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()

        # Fetch drug names
        all_ids = {r.drug_id_1 for r in rows} | {r.drug_id_2 for r in rows}
        drug_names: dict[str, str] = {}
        if all_ids:
            drugs = (await self.db.execute(select(Drug).where(Drug.id.in_(all_ids)))).scalars().all()
            drug_names = {d.id: d.name for d in drugs}

        items = [
            DrugInteractionResponse(
                id=r.id,
                drug_id_1=r.drug_id_1,
                drug_id_2=r.drug_id_2,
                interaction_type=r.interaction_type,
                severity=r.severity,
                description=r.description,
                recommendation=r.recommendation,
                drug_1_name=drug_names.get(r.drug_id_1),
                drug_2_name=drug_names.get(r.drug_id_2),
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
        # Verify both drugs exist
        for did in [data.drug_id_1, data.drug_id_2]:
            exists = await self.db.scalar(select(func.count(Drug.id)).where(Drug.id == did))
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Thuốc '{did}' không tìm thấy",
                )

        # Check duplicate
        existing = await self.db.scalar(
            select(DrugInteraction).where(
                and_(
                    DrugInteraction.drug_id_1 == data.drug_id_1,
                    DrugInteraction.drug_id_2 == data.drug_id_2,
                )
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tương tác giữa 2 thuốc này đã tồn tại",
            )

        interaction = DrugInteraction(
            drug_id_1=data.drug_id_1,
            drug_id_2=data.drug_id_2,
            interaction_type=data.interaction_type,
            severity=InteractionSeverity(data.severity),
            description=data.description,
            recommendation=data.recommendation,
        )
        self.db.add(interaction)
        await self.db.flush()
        await self._invalidate_interaction_cache(data.drug_id_1, data.drug_id_2)
        return interaction

    async def update(self, interaction_id: int, data: AdminInteractionUpdate) -> DrugInteraction:
        interaction = await self.db.scalar(
            select(DrugInteraction).where(DrugInteraction.id == interaction_id)
        )
        if not interaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tương tác không tìm thấy")

        if data.interaction_type is not None:
            interaction.interaction_type = data.interaction_type
        if data.severity is not None:
            interaction.severity = InteractionSeverity(data.severity)
        if data.description is not None:
            interaction.description = data.description
        if data.recommendation is not None:
            interaction.recommendation = data.recommendation

        await self.db.flush()
        await self._invalidate_interaction_cache(interaction.drug_id_1, interaction.drug_id_2)
        return interaction

    async def delete(self, interaction_id: int) -> None:
        interaction = await self.db.scalar(
            select(DrugInteraction).where(DrugInteraction.id == interaction_id)
        )
        if not interaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tương tác không tìm thấy")

        await self._invalidate_interaction_cache(interaction.drug_id_1, interaction.drug_id_2)
        await self.db.delete(interaction)
        await self.db.flush()
