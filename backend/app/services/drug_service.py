from __future__ import annotations

import json
import logging
from io import BytesIO
from itertools import combinations
from math import ceil
from typing import List, Optional

import openpyxl
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drug import Drug, DrugInteraction
from app.schemas.drug import (
    DrugDetailResponse,
    DrugInteractionResponse,
    DrugEventTypeResponse,
    DrugListItem,
    InteractionCheckResult,
    SafePairInfo,
)
from app.schemas.user import PaginatedResponse, PaginationMeta

logger = logging.getLogger(__name__)

_LIST_TTL = 300    # 5 phút
_DETAIL_TTL = 600  # 10 phút
_PAIR_TTL = 1800   # 30 phút


# ══════════════════════════════════════════════════════════════════════════════
#  DrugService
# ══════════════════════════════════════════════════════════════════════════════

class DrugService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def get_list(
        self,
        page: int,
        size: int,
        search: Optional[str] = None,
    ) -> PaginatedResponse:
        cache_key = f"cache:drugs:list:{page}:{size}:{search or ''}"
        cached = await self.redis.get(cache_key)
        if cached:
            return PaginatedResponse.model_validate_json(cached)

        stmt = select(Drug)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Drug.generic_name.ilike(term),
                    Drug.id.ilike(term),
                )
            )

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        stmt = stmt.order_by(Drug.generic_name.asc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        drugs = result.scalars().all()

        response = PaginatedResponse(
            items=[DrugListItem.model_validate(d) for d in drugs],
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )
        await self.redis.setex(cache_key, _LIST_TTL, response.model_dump_json())
        return response

    async def get_by_id(self, drug_id: str) -> DrugDetailResponse:
        cache_key = f"cache:drug:{drug_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return DrugDetailResponse.model_validate_json(cached)

        result = await self.db.execute(
            select(Drug)
            .where(Drug.id == drug_id)
            .options(
                selectinload(Drug.brand_names),
                selectinload(Drug.warnings),
                selectinload(Drug.dosage_forms),
                selectinload(Drug.categories),
                selectinload(Drug.atc_codes),
            )
        )
        drug = result.scalar_one_or_none()
        if not drug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thuốc '{drug_id}' không tìm thấy",
            )

        response = DrugDetailResponse.from_orm_drug(drug)
        await self.redis.setex(cache_key, _DETAIL_TTL, response.model_dump_json())
        return response

    async def get_drug_interactions(
        self, drug_id: str, page: int, size: int
    ) -> PaginatedResponse:
        exists = await self.db.scalar(select(func.count()).where(Drug.id == drug_id))
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thuốc '{drug_id}' không tìm thấy",
            )

        stmt = select(DrugInteraction).where(DrugInteraction.drug_id == drug_id)
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))

        result = await self.db.execute(
            stmt.order_by(DrugInteraction.interacts_with_id.asc())
            .offset((page - 1) * size)
            .limit(size)
        )
        interactions = result.scalars().all()

        # Fetch tên thuốc chính
        drug_result = await self.db.scalar(select(Drug).where(Drug.id == drug_id))
        drug_name = drug_result.generic_name if drug_result else None

        items = [
            DrugInteractionResponse(
                drug_id=i.drug_id,
                interacts_with_id=i.interacts_with_id,
                interacts_with_name=i.interacts_with_name,
                drug_name=drug_name,
            )
            for i in interactions
        ]
        return PaginatedResponse(
            items=items,
            meta=PaginationMeta(
                total=total, page=page, size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )

    async def invalidate_drug_cache(self, drug_id: str) -> None:
        await self.redis.delete(f"cache:drug:{drug_id}")
        async for key in self.redis.scan_iter("cache:drugs:list:*"):
            await self.redis.delete(key)
        logger.info(f"Invalidated cache for drug {drug_id}")


# ══════════════════════════════════════════════════════════════════════════════
#  InteractionService
# ══════════════════════════════════════════════════════════════════════════════

class InteractionService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def check_interactions(self, drug_ids: List[str]) -> InteractionCheckResult:
        from app.models.drug_event_type import DrugEventType
        from app.models.drug_feature import DrugFeature
        from app.models.drug import InteractionSource
        from app.services.ml_client import predict_interaction

        # ── Step 1: Validate all drug IDs exist ─────────────────────────────
        drugs_result = await self.db.execute(select(Drug).where(Drug.id.in_(drug_ids)))
        found_drugs = {d.id: d.generic_name for d in drugs_result.scalars().all()}
        missing = [d for d in drug_ids if d not in found_drugs]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Thuốc không tìm thấy trong hệ thống: {', '.join(missing)}",
            )

        # ── Step 2: Build pairs ──────────────────────────────────────────────
        original_pairs = list(combinations(drug_ids, 2))
        all_directed: list[tuple] = []
        for a, b in original_pairs:
            all_directed.append((a, b))
            all_directed.append((b, a))

        # ── Step 3: Redis cache check ────────────────────────────────────────
        pair_results: dict[tuple, Optional[dict]] = {}
        uncached_pairs: list[tuple] = []

        for pair in all_directed:
            cache_key = f"cache:interaction:{pair[0]}:{pair[1]}"
            cached = await self.redis.get(cache_key)
            if cached is not None:
                pair_results[pair] = None if cached == "null" else json.loads(cached)
            else:
                uncached_pairs.append(pair)

        # ── Step 4: Batch DB lookup ──────────────────────────────────────────
        if uncached_pairs:
            conditions = [
                and_(
                    DrugInteraction.drug_id == a,
                    DrugInteraction.interacts_with_id == b,
                )
                for a, b in uncached_pairs
            ]
            result = await self.db.execute(
                select(DrugInteraction)
                .options(selectinload(DrugInteraction.event_type))
                .where(or_(*conditions))
            )
            db_map = {
                (i.drug_id, i.interacts_with_id): i
                for i in result.scalars().all()
            }

            for pair in uncached_pairs:
                cache_key = f"cache:interaction:{pair[0]}:{pair[1]}"
                interaction = db_map.get(pair)
                if interaction:
                    data = {
                        "drug_id": interaction.drug_id,
                        "interacts_with_id": interaction.interacts_with_id,
                        "interacts_with_name": interaction.interacts_with_name,
                        "event_type_id": interaction.event_type_id,
                        "interaction_label": interaction.interaction_label,
                        "source": interaction.source.value if interaction.source else "database",
                        "confidence_score": interaction.confidence_score,
                        "event_type": {
                            "id": interaction.event_type.id,
                            "event_name": interaction.event_type.event_name,
                            "description": interaction.event_type.description,
                            "source_event_id": interaction.event_type.source_event_id,
                        } if interaction.event_type else None,
                    }
                    await self.redis.setex(cache_key, _PAIR_TTL, json.dumps(data))
                    pair_results[pair] = data
                else:
                    await self.redis.setex(cache_key, _PAIR_TTL, "null")
                    pair_results[pair] = None

        # ── Step 5: Find canonical pairs needing ML ──────────────────────────
        pairs_needing_ml: list[tuple] = []
        for a, b in original_pairs:
            if pair_results.get((a, b)) is None and pair_results.get((b, a)) is None:
                pairs_needing_ml.append((a, b))

        # ── Step 6: ML fallback ──────────────────────────────────────────────
        from app.config import settings
        ml_interactions: list[DrugInteractionResponse] = []
        prediction_count = 0

        if pairs_needing_ml:
            all_ml_ids = {d for pair in pairs_needing_ml for d in pair}
            feat_result = await self.db.execute(
                select(DrugFeature).where(DrugFeature.drug_id.in_(all_ml_ids))
            )
            features_map = {f.drug_id: f for f in feat_result.scalars().all()}

            event_type_result = await self.db.execute(select(DrugEventType))
            event_type_map = {et.event_name: et for et in event_type_result.scalars().all()}

            for a, b in pairs_needing_ml:
                feat_a = features_map.get(a)
                feat_b = features_map.get(b)
                if not feat_a or not feat_b:
                    continue

                prediction = await predict_interaction(
                    drug_a_id=a,
                    drug_b_id=b,
                    features_a={
                        "targets": feat_a.targets,
                        "enzymes": feat_a.enzymes,
                        "pathways": feat_a.pathways,
                        "smiles": feat_a.smiles,
                    },
                    features_b={
                        "targets": feat_b.targets,
                        "enzymes": feat_b.enzymes,
                        "pathways": feat_b.pathways,
                        "smiles": feat_b.smiles,
                    },
                )
                if prediction is None:
                    continue

                predicted_event_name = prediction.get("event_name", "")
                confidence = prediction.get("confidence")
                event_type = event_type_map.get(predicted_event_name)

                if settings.ML_CACHE_PREDICTIONS:
                    new_row = DrugInteraction(
                        drug_id=a,
                        interacts_with_id=b,
                        interacts_with_name=found_drugs.get(b),
                        event_type_id=event_type.id if event_type else None,
                        interaction_label=predicted_event_name,
                        source=InteractionSource.model_predicted,
                        confidence_score=confidence,
                    )
                    self.db.add(new_row)
                    cache_data = {
                        "drug_id": a,
                        "interacts_with_id": b,
                        "interacts_with_name": found_drugs.get(b),
                        "event_type_id": event_type.id if event_type else None,
                        "interaction_label": predicted_event_name,
                        "source": "model_predicted",
                        "confidence_score": confidence,
                        "event_type": {
                            "id": event_type.id,
                            "event_name": event_type.event_name,
                            "description": event_type.description,
                            "source_event_id": event_type.source_event_id,
                        } if event_type else None,
                    }
                    await self.redis.setex(
                        f"cache:interaction:{a}:{b}", _PAIR_TTL, json.dumps(cache_data)
                    )
                    await self.db.commit()

                prediction_count += 1
                ml_interactions.append(DrugInteractionResponse(
                    drug_id=a,
                    interacts_with_id=b,
                    interacts_with_name=found_drugs.get(b),
                    drug_name=found_drugs.get(a),
                    event_type_id=event_type.id if event_type else None,
                    interaction_label=predicted_event_name,
                    source="model_predicted",
                    confidence_score=confidence,
                    event_type=DrugEventTypeResponse.model_validate(event_type) if event_type else None,
                ))

        # ── Step 7: Consolidate DB interactions ──────────────────────────────
        seen_pairs: set[frozenset] = set()
        db_interactions: list[DrugInteractionResponse] = []
        interacting_drug_sets: set[frozenset] = set()

        for pair in all_directed:
            data = pair_results.get(pair)
            if not data:
                continue
            key = frozenset([pair[0], pair[1]])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            interacting_drug_sets.add(key)
            db_interactions.append(DrugInteractionResponse(
                drug_id=data["drug_id"],
                interacts_with_id=data["interacts_with_id"],
                interacts_with_name=data.get("interacts_with_name"),
                drug_name=found_drugs.get(data["drug_id"]),
                event_type_id=data.get("event_type_id"),
                interaction_label=data.get("interaction_label"),
                source=data.get("source"),
                confidence_score=data.get("confidence_score"),
                event_type=DrugEventTypeResponse(**data["event_type"])
                    if data.get("event_type") else None,
            ))

        for ml_ix in ml_interactions:
            interacting_drug_sets.add(frozenset([ml_ix.drug_id, ml_ix.interacts_with_id]))

        all_interactions = db_interactions + ml_interactions

        # ── Step 8: Safe pairs ────────────────────────────────────────────────
        safe_pairs = [
            SafePairInfo(
                drug_id_1=a,
                drug_id_2=b,
                drug_1_name=found_drugs.get(a),
                drug_2_name=found_drugs.get(b),
            )
            for a, b in original_pairs
            if frozenset([a, b]) not in interacting_drug_sets
        ]

        return InteractionCheckResult(
            checked_drugs=drug_ids,
            total_pairs=len(original_pairs),
            has_interaction=len(all_interactions) > 0,
            interactions=all_interactions,
            safe_pairs=safe_pairs,
            prediction_count=prediction_count,
        )

    async def export_result(self, drug_ids: List[str]) -> bytes:
        result = await self.check_interactions(drug_ids)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Tương tác thuốc"

        headers = ["STT", "Thuốc A (ID)", "Thuốc B (ID)", "Tên thuốc B", "Loại tương tác", "Nguồn", "Độ tin cậy"]
        ws.append(headers)
        for col, _ in enumerate(headers, 1):
            ws.cell(row=1, column=col).font = openpyxl.styles.Font(bold=True)

        for i, interaction in enumerate(result.interactions, 1):
            ws.append([
                i,
                interaction.drug_id,
                interaction.interacts_with_id,
                interaction.interacts_with_name or "",
                interaction.interaction_label or "",
                interaction.source or "database",
                f"{interaction.confidence_score:.2%}" if interaction.confidence_score is not None else "",
            ])

        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()
