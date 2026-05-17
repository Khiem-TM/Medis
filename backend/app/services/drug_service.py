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
_EXPLAIN_TTL = 86400  # 24 giờ


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
                interaction_label=i.interaction_label,
                source=i.source.value if i.source else "database",
                confidence_score=i.confidence_score,
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
                        "generic_name": found_drugs.get(a),
                        "targets": feat_a.targets,
                        "enzymes": feat_a.enzymes,
                        "pathways": feat_a.pathways,
                        "smiles": feat_a.smiles,
                    },
                    features_b={
                        "generic_name": found_drugs.get(b),
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


# ══════════════════════════════════════════════════════════════════════════════
#  InteractionExplainService
# ══════════════════════════════════════════════════════════════════════════════

class InteractionExplainService:
    SYSTEM_PROMPT = """Bạn là dược sĩ lâm sàng chuyên giải thích tương tác thuốc cho người dùng phổ thông Việt Nam.

NGUYÊN TẮC BẮT BUỘC:
- Ngôn ngữ: Tiếng Việt hoàn toàn, cấp độ phổ thông (tránh thuật ngữ Latin nếu không có giải thích kèm)
- Không phóng đại, không gây hoảng loạn không cần thiết
- Chỉ dựa vào dữ liệu được cung cấp, không bịa thêm thông tin
- Nếu nguồn là "model_predicted", hãy ghi rõ độ tin cậy trong confidence_note
- Trả về JSON ONLY, đúng schema sau, không có text ngoài JSON:

{
  "severity": "Nghiêm trọng" | "Cần chú ý" | "Nhẹ",
  "severity_color": "red" | "amber" | "yellow",
  "summary": "<1 câu tóm tắt ngắn gọn nhất, tối đa 120 ký tự>",
  "mechanism": "<giải thích cơ chế 2-3 câu, dùng ngôn ngữ đơn giản>",
  "symptoms_to_watch": ["<triệu chứng 1>", "<triệu chứng 2>"],
  "what_to_do": ["<hành động cụ thể 1>", "<hành động cụ thể 2>"],
  "when_to_see_doctor": "<mô tả tình huống khẩn cấp cần gặp bác sĩ>",
  "can_be_used_together": true | false | null,
  "confidence_note": "<chỉ điền nếu nguồn là model_predicted, null nếu database>"
}"""

    USER_PROMPT_TEMPLATE = """Giải thích tương tác giữa 2 thuốc sau:

THUỐC A: {drug_a_name}
- Nhóm dược lý: {drug_a_categories}
- Cơ chế tác dụng (targets): {drug_a_targets}
- Enzyme chuyển hóa: {drug_a_enzymes}
- Cảnh báo an toàn đã biết: {drug_a_warnings}

THUỐC B: {drug_b_name}
- Nhóm dược lý: {drug_b_categories}
- Cơ chế tác dụng (targets): {drug_b_targets}
- Enzyme chuyển hóa: {drug_b_enzymes}
- Cảnh báo an toàn đã biết: {drug_b_warnings}

DỮ LIỆU TƯƠNG TÁC ĐÃ PHÁT HIỆN:
- Loại sự kiện: {event_name}
- Mô tả sự kiện: {event_description}
- Nhãn tương tác: {interaction_label}
- Nguồn dữ liệu: {source_note}
{confidence_line}

Hãy giải thích tương tác này theo JSON schema đã quy định."""

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        from app.services.gemini_client import build_gemini_client
        self.client = build_gemini_client()

    def _normalize_ids(self, id1: str, id2: str) -> tuple[str, str]:
        return (id1, id2) if id1 <= id2 else (id2, id1)

    def _cache_key(self, id1: str, id2: str) -> str:
        a, b = self._normalize_ids(id1, id2)
        return f"cache:interaction_explain:{a}:{b}"

    async def explain(self, drug_id_1: str, drug_id_2: str) -> "InteractionExplainResponse":
        from app.schemas.interaction_explain import InteractionExplainResponse
        from app.models.drug import DrugInteraction
        from app.models.drug_event_type import DrugEventType
        from app.models.drug_feature import DrugFeature

        cache_key = self._cache_key(drug_id_1, drug_id_2)
        cached = await self.redis.get(cache_key)
        if cached:
            resp = InteractionExplainResponse.model_validate_json(cached)
            resp.from_cache = True
            return resp

        drug_service = DrugService(self.db, self.redis)
        try:
            drug_a = await drug_service.get_by_id(drug_id_1)
            drug_b = await drug_service.get_by_id(drug_id_2)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy một hoặc cả hai thuốc",
            )

        feat_a_result = await self.db.execute(
            select(DrugFeature).where(DrugFeature.drug_id == drug_id_1)
        )
        feat_a = feat_a_result.scalar_one_or_none()

        feat_b_result = await self.db.execute(
            select(DrugFeature).where(DrugFeature.drug_id == drug_id_2)
        )
        feat_b = feat_b_result.scalar_one_or_none()

        interaction_result = await self.db.execute(
            select(DrugInteraction)
            .where(
                or_(
                    and_(
                        DrugInteraction.drug_id == drug_id_1,
                        DrugInteraction.interacts_with_id == drug_id_2,
                    ),
                    and_(
                        DrugInteraction.drug_id == drug_id_2,
                        DrugInteraction.interacts_with_id == drug_id_1,
                    ),
                )
            )
            .options(selectinload(DrugInteraction.event_type))
            .limit(1)
        )
        interaction = interaction_result.scalar_one_or_none()
        event_type: DrugEventType | None = interaction.event_type if interaction else None

        def fmt_list(items, fallback: str = "Không có thông tin") -> str:
            return ", ".join(items) if items else fallback

        def truncate(text: str | None, max_chars: int = 300) -> str:
            if not text:
                return "Không có thông tin"
            return text[:max_chars] + "..." if len(text) > max_chars else text

        event_name = "Không xác định"
        event_description = "Không có mô tả"
        interaction_label = "Không xác định"
        source = "database"
        confidence_score = None

        if interaction:
            interaction_label = interaction.interaction_label or "Không xác định"
            source = interaction.source.value if interaction.source else "database"
            confidence_score = interaction.confidence_score
            if event_type:
                event_name = event_type.event_name or "Không xác định"
                event_description = event_type.description or "Không có mô tả"

        source_note = (
            "Dữ liệu từ cơ sở dữ liệu dược học đã được xác minh"
            if source == "database"
            else "Dự đoán từ mô hình AI (chưa được xác minh lâm sàng đầy đủ)"
        )
        confidence_line = (
            f"- Độ tin cậy của dự đoán: {confidence_score:.0%}"
            if confidence_score is not None else ""
        )

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            drug_a_name=drug_a.generic_name,
            drug_a_categories=fmt_list(drug_a.categories),
            drug_a_targets=truncate(feat_a.targets if feat_a else None),
            drug_a_enzymes=truncate(feat_a.enzymes if feat_a else None),
            drug_a_warnings=fmt_list(
                [w.warning_text for w in drug_a.warnings],
                "Không có cảnh báo đặc biệt",
            ),
            drug_b_name=drug_b.generic_name,
            drug_b_categories=fmt_list(drug_b.categories),
            drug_b_targets=truncate(feat_b.targets if feat_b else None),
            drug_b_enzymes=truncate(feat_b.enzymes if feat_b else None),
            drug_b_warnings=fmt_list(
                [w.warning_text for w in drug_b.warnings],
                "Không có cảnh báo đặc biệt",
            ),
            event_name=event_name,
            event_description=event_description,
            interaction_label=interaction_label,
            source_note=source_note,
            confidence_line=confidence_line,
        )

        llm_data = await self._call_llm(user_prompt)
        response = InteractionExplainResponse(
            drug_a_id=drug_id_1,
            drug_b_id=drug_id_2,
            drug_a_name=drug_a.generic_name,
            drug_b_name=drug_b.generic_name,
            source=source,
            from_cache=False,
            **llm_data,
        )

        await self.redis.setex(cache_key, _EXPLAIN_TTL, response.model_dump_json())
        return response

    async def _call_llm(self, user_prompt: str) -> dict:
        if not self.client:
            return self._fallback_response("Dịch vụ Gemini chưa được cấu hình")

        try:
            raw = await self.client.generate_text(
                self.SYSTEM_PROMPT,
                [{"role": "user", "content": user_prompt}],
                temperature=0.2,
                max_tokens=800,
            )
            data = json.loads(self._extract_json(raw))
            self._validate_llm_data(data)
            allowed = {
                "severity",
                "severity_color",
                "summary",
                "mechanism",
                "symptoms_to_watch",
                "what_to_do",
                "when_to_see_doctor",
                "can_be_used_together",
                "confidence_note",
            }
            return {key: data.get(key) for key in allowed if key in data}
        except Exception as e:
            logger.warning(f"InteractionExplainService LLM error: {e}")
            return self._fallback_response()

    def _extract_json(self, raw: str) -> str:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Gemini response does not contain a JSON object")
        return text[start:end + 1]

    def _validate_llm_data(self, data: dict) -> None:
        required = {
            "severity",
            "severity_color",
            "summary",
            "mechanism",
            "symptoms_to_watch",
            "what_to_do",
            "when_to_see_doctor",
            "can_be_used_together",
        }
        if not required.issubset(data.keys()):
            raise ValueError("Missing required keys in LLM response")
        if data["severity"] not in {"Nghiêm trọng", "Cần chú ý", "Nhẹ"}:
            raise ValueError("Invalid severity in LLM response")
        if data["severity_color"] not in {"red", "amber", "yellow"}:
            raise ValueError("Invalid severity_color in LLM response")
        if not isinstance(data["symptoms_to_watch"], list):
            raise ValueError("Invalid symptoms_to_watch in LLM response")
        if not isinstance(data["what_to_do"], list):
            raise ValueError("Invalid what_to_do in LLM response")
        if data["can_be_used_together"] not in {True, False, None}:
            raise ValueError("Invalid can_be_used_together in LLM response")

    def _fallback_response(self, note: str = "") -> dict:
        return {
            "severity": "Cần chú ý",
            "severity_color": "amber",
            "summary": "Không thể tạo giải thích tự động. Vui lòng tham khảo dược sĩ.",
            "mechanism": note or "Hệ thống giải thích tạm thời không khả dụng.",
            "symptoms_to_watch": [],
            "what_to_do": [
                "Tham khảo ý kiến dược sĩ hoặc bác sĩ trước khi dùng đồng thời hai thuốc này."
            ],
            "when_to_see_doctor": "Khi có bất kỳ triệu chứng bất thường nào sau khi dùng thuốc.",
            "can_be_used_together": None,
            "confidence_note": None,
        }
