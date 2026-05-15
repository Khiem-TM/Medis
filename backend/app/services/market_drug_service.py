from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from datetime import datetime
from typing import Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drug import Drug, DrugInteraction, InteractionSource
from app.models.drug_feature import DrugFeature
from app.models.market_drug import MarketDrugProduct, MarketDrugProductIngredient
from app.schemas.market_drug import (
    MarketDrugImportResult,
    MarketDrugProductDetail,
    MarketDrugProductListItem,
    MarketInteractionCheckResult,
    ProductIngredientInfo,
)
from app.schemas.user import PaginatedResponse, PaginationMeta

logger = logging.getLogger(__name__)

DAV_SEARCH_URL = "https://dichvucong.dav.gov.vn/api/services/app/soDangKy/GetAllPublicServerPaging"
DEFAULT_IMPORT_TERMS = ["aspirin", "ibuprofen", "warfarin", "paracetamol"]
IMAGE_MAP = {
    "aspirin": "/static/market_drugs/tablet-box-red.svg",
    "ibuprofen": "/static/market_drugs/tablet-box-blue.svg",
    "warfarin": "/static/market_drugs/blister-green.svg",
    "paracetamol": "/static/market_drugs/tablet-box-blue.svg",
}
DEMO_DDI_DRUGS = [
    {
        "id": "DB00945",
        "generic_name": "Acetylsalicylicacid",
        "description": "Demo canonical drug for Aspirin / acetylsalicylic acid.",
        "features": {
            "targets": "Prostaglandin G/H synthase 1, Prostaglandin G/H synthase 2",
            "enzymes": "Cytochrome P450 2C9",
            "pathways": "Aspirin Action Pathway",
            "smiles": "CC(=O)OC1=CC=CC=C1C(O)=O",
        },
    },
    {
        "id": "DB00682",
        "generic_name": "Warfarin",
        "description": "Demo canonical drug for Warfarin.",
        "features": {
            "targets": "Vitamin K epoxide reductase complex subunit 1",
            "enzymes": "Cytochrome P450 2C9",
            "pathways": "Warfarin Action Pathway",
            "smiles": "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O",
        },
    },
    {
        "id": "DB01050",
        "generic_name": "Ibuprofen",
        "description": "Demo canonical drug for Ibuprofen.",
        "features": {
            "targets": "Prostaglandin G/H synthase 1, Prostaglandin G/H synthase 2",
            "enzymes": "Cytochrome P450 2C9, Cytochrome P450 2C19",
            "pathways": "Ibuprofen Action Pathway",
            "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O",
        },
    },
    {
        "id": "DB00316",
        "generic_name": "Acetaminophen",
        "description": "Demo canonical drug for Paracetamol / Acetaminophen.",
        "features": {
            "targets": "Prostaglandin G/H synthase 1, Prostaglandin G/H synthase 2",
            "enzymes": "Cytochrome P450 2E1, Cytochrome P450 1A2",
            "pathways": "Acetaminophen Action Pathway",
            "smiles": "CC(=O)NC1=CC=C(O)C=C1",
        },
    },
]
DEMO_INGREDIENT_DDI_MAP = {
    "aspirin": "DB00945",
    "acetylsalicylic acid": "DB00945",
    "ibuprofen": "DB01050",
    "warfarin": "DB00682",
    "warfarin sodium": "DB00682",
    "warfarin natri": "DB00682",
    "paracetamol": "DB00316",
    "acetaminophen": "DB00316",
}
DEMO_INTERACTIONS = [
    ("DB00682", "DB00945", "Tăng nguy cơ chảy máu khi phối hợp warfarin với aspirin."),
    ("DB00682", "DB01050", "Tăng nguy cơ chảy máu tiêu hoá khi phối hợp warfarin với ibuprofen."),
    ("DB00945", "DB01050", "Ibuprofen có thể làm giảm tác dụng chống kết tập tiểu cầu của aspirin liều thấp."),
]


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.lower()
    value = re.sub(r"\(.*?\)", " ", value)
    value = re.sub(r"\b\d+[.,]?\d*\s*(mg|mcg|g|ml|%|ui|iu)\b", " ", value)
    value = re.sub(r"[/;+]", " ", value)
    value = re.sub(
        r"\b(dang|duoi dang|tuong duong|hydrochloride|hydrochlorid|hcl|natri|sodium|clathrate|clatrat|bisulphat)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9\s-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _extract_ingredient_parts(raw_text: str) -> list[tuple[str, str, Optional[str]]]:
    if not raw_text:
        return []
    parts = re.split(r"[;,]", raw_text)
    results: list[tuple[str, str, Optional[str]]] = []
    for part in parts:
        cleaned = part.strip()
        if not cleaned:
            continue
        strength_match = re.search(r"(\d+[.,]?\d*\s*(?:mg|mcg|g|ml|%|UI|IU))", cleaned, flags=re.IGNORECASE)
        strength = strength_match.group(1) if strength_match else None
        name = cleaned
        if strength_match:
            name = cleaned[: strength_match.start()].strip() or cleaned
        normalized = _normalize_text(name)
        if normalized:
            results.append((cleaned, normalized, strength))
    return results


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class MarketDrugService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_products(self, page: int, size: int, search: Optional[str] = None) -> PaginatedResponse:
        stmt = select(MarketDrugProduct).options(
            selectinload(MarketDrugProduct.ingredients).selectinload(MarketDrugProductIngredient.ddi_drug),
        )
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    MarketDrugProduct.product_name.ilike(term),
                    MarketDrugProduct.registration_number.ilike(term),
                    MarketDrugProduct.normalized_product_name.ilike(term),
                )
            )

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        result = await self.db.execute(
            stmt.order_by(MarketDrugProduct.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = [await self._to_list_item(p) for p in result.scalars().all()]
        return PaginatedResponse(
            items=items,
            meta=PaginationMeta(total=total, page=page, size=size, total_pages=max(1, (total + size - 1) // size)),
        )

    async def get_product_by_id(self, product_id: int) -> MarketDrugProductDetail:
        result = await self.db.execute(
            select(MarketDrugProduct)
            .where(MarketDrugProduct.id == product_id)
            .options(
                selectinload(MarketDrugProduct.ingredients).selectinload(MarketDrugProductIngredient.ddi_drug),
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thuốc thị trường")
        return await self._to_detail_item(product)

    async def check_market_product_interactions(
        self, product_ids: list[int], redis
    ) -> MarketInteractionCheckResult:
        from app.services.drug_service import InteractionService

        rows = (
            await self.db.execute(
                select(MarketDrugProduct)
                .where(MarketDrugProduct.id.in_(product_ids))
                .options(selectinload(MarketDrugProduct.ingredients))
            )
        ).scalars().all()

        found_map = {p.id: p for p in rows}
        missing = [pid for pid in product_ids if pid not in found_map]
        if missing:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không tìm thấy sản phẩm: {missing}",
            )

        products_info: list[ProductIngredientInfo] = []
        unmapped: list[int] = []
        all_ddi_ids: list[str] = []

        for pid in product_ids:
            product = found_map[pid]
            ddi_ids = sorted({
                ing.ddi_drug_id
                for ing in product.ingredients
                if ing.ddi_drug_id
            })
            if not ddi_ids:
                unmapped.append(pid)
            else:
                all_ddi_ids.extend(ddi_ids)
            products_info.append(ProductIngredientInfo(
                product_id=pid,
                product_name=product.product_name,
                ddi_drug_ids=ddi_ids,
            ))

        unique_ddi_ids = list(dict.fromkeys(all_ddi_ids))

        ddi_result = None
        if len(unique_ddi_ids) >= 2:
            interaction_svc = InteractionService(self.db, redis)
            check = await interaction_svc.check_interactions(unique_ddi_ids)
            ddi_result = check.model_dump()

        return MarketInteractionCheckResult(
            products=products_info,
            unmapped_products=unmapped,
            ddi_result=ddi_result,
        )

    async def resolve_market_product_drug_ids(self, market_product_id: int) -> list[str]:
        rows = (
            await self.db.execute(
                select(MarketDrugProductIngredient)
                .where(MarketDrugProductIngredient.market_product_id == market_product_id)
                .order_by(MarketDrugProductIngredient.sort_order.asc(), MarketDrugProductIngredient.id.asc())
            )
        ).scalars().all()
        return sorted({row.ddi_drug_id for row in rows if row.ddi_drug_id})

    async def import_demo_products(self, limit_per_term: int = 2) -> MarketDrugImportResult:
        await self._seed_demo_ddi_data()

        imported_count = 0
        updated_count = 0
        mapped_ingredients = 0
        imported_products: list[MarketDrugProductListItem] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for term in DEFAULT_IMPORT_TERMS:
                payload = {
                    "skipCount": 0,
                    "maxResultCount": limit_per_term,
                    "sorting": None,
                    "filterText": term,
                    "SoDangKyThuoc": {},
                    "KichHoat": True,
                }
                response = await client.post(DAV_SEARCH_URL, json=payload)
                response.raise_for_status()
                records = response.json().get("result", {}).get("items", [])
                for record in records:
                    product, created, mapped_count = await self._upsert_dav_product(record)
                    if created:
                        imported_count += 1
                    else:
                        updated_count += 1
                    mapped_ingredients += mapped_count
                    imported_products.append(await self._to_list_item(product))

        await self.db.flush()
        return MarketDrugImportResult(
            imported_count=imported_count,
            updated_count=updated_count,
            mapped_ingredients=mapped_ingredients,
            imported_products=imported_products,
        )

    async def _seed_demo_ddi_data(self) -> None:
        for item in DEMO_DDI_DRUGS:
            drug = await self.db.scalar(select(Drug).where(Drug.id == item["id"]))
            if not drug:
                drug = Drug(
                    id=item["id"],
                    generic_name=item["generic_name"],
                    description=item["description"],
                )
                self.db.add(drug)
                await self.db.flush()
            features = await self.db.scalar(select(DrugFeature).where(DrugFeature.drug_id == item["id"]))
            if not features:
                self.db.add(DrugFeature(drug_id=item["id"], **item["features"]))

        for a, b, label in DEMO_INTERACTIONS:
            for source_id, target_id in ((a, b), (b, a)):
                interaction = await self.db.scalar(
                    select(DrugInteraction).where(
                        DrugInteraction.drug_id == source_id,
                        DrugInteraction.interacts_with_id == target_id,
                    )
                )
                if not interaction:
                    target_drug = await self.db.scalar(select(Drug).where(Drug.id == target_id))
                    self.db.add(
                        DrugInteraction(
                            drug_id=source_id,
                            interacts_with_id=target_id,
                            interacts_with_name=target_drug.generic_name if target_drug else target_id,
                            interaction_label=label,
                            source=InteractionSource.database,
                        )
                    )

        await self.db.flush()

    async def _upsert_dav_product(self, record: dict) -> tuple[MarketDrugProduct, bool, int]:
        registration_number = (record.get("soDangKy") or "").strip()
        if not registration_number:
            raise HTTPException(status_code=400, detail="Bản ghi DAV không có số đăng ký")

        existing = await self.db.scalar(
            select(MarketDrugProduct).where(MarketDrugProduct.registration_number == registration_number)
        )
        created = existing is None
        product = existing or MarketDrugProduct(registration_number=registration_number)
        if created:
            self.db.add(product)

        basic = record.get("thongTinThuocCoBan") or {}
        reg = record.get("thongTinDangKyThuoc") or {}
        product.source_product_id = record.get("id")
        product.old_registration_number = record.get("soDangKyCu") or None
        product.product_name = record.get("tenThuoc") or registration_number
        product.normalized_product_name = _normalize_text(product.product_name)
        product.dosage_form = basic.get("dangBaoChe") or record.get("dangBaoChe")
        product.packaging = basic.get("dongGoi") or record.get("dongGoi")
        product.route_name = basic.get("tenDuongDung")
        product.quality_standard = basic.get("tieuChuan") or record.get("tieuChuan")
        product.shelf_life = basic.get("tuoiTho") or record.get("tuoiTho")
        product.decision_number = reg.get("soQuyetDinh") or record.get("soQuyetDinh")
        product.issue_batch = reg.get("dotCap") or record.get("dotCap")
        product.registration_date = _parse_dt(reg.get("ngayCapSoDangKy") or record.get("ngayCapSoDangKy"))
        product.expiry_date = _parse_dt(reg.get("ngayHetHanSoDangKy"))
        product.is_expired = bool(record.get("isHetHan"))
        product.is_withdrawn = bool(record.get("isDaRutSoDangKy"))
        product.is_active = bool(record.get("isActive", True))
        product.raw_ingredients_text = basic.get("hoatChatChinh") or record.get("hoatChatChinh")
        product.image_url = self._pick_demo_image(product)
        product.source_payload = record
        product.source_payload_hash = hashlib.sha256(str(record).encode("utf-8")).hexdigest()
        product.last_synced_at = datetime.now()
        await self.db.flush()

        mapped_count = await self._replace_product_ingredients(product)
        return product, created, mapped_count

    async def _replace_product_ingredients(self, product: MarketDrugProduct) -> int:
        rows = (
            await self.db.execute(
                select(MarketDrugProductIngredient).where(MarketDrugProductIngredient.market_product_id == product.id)
            )
        ).scalars().all()
        for row in rows:
            await self.db.delete(row)
        await self.db.flush()

        # Cache all drug generic names for mapping
        drugs_result = await self.db.execute(select(Drug))
        all_drugs = drugs_result.scalars().all()
        drug_map = {d.generic_name.lower(): d.id for d in all_drugs}

        mapped_count = 0
        for idx, (raw_name, normalized_name, strength) in enumerate(_extract_ingredient_parts(product.raw_ingredients_text or "")):
            # Try DEMO map first
            ddi_drug_id = DEMO_INGREDIENT_DDI_MAP.get(normalized_name)
            
            # Fallback to dynamic db match using a more flexible substring matching
            if not ddi_drug_id and normalized_name:
                norm_lower = normalized_name.lower()
                # Try exact match first
                ddi_drug_id = drug_map.get(norm_lower)
                
                # If no exact match, try substring match (drug name inside ingredient name)
                if not ddi_drug_id:
                    for drug_name, d_id in drug_map.items():
                        # To avoid short generic matches like "c" or "a", ensure drug_name is reasonably long
                        if len(drug_name) > 3 and drug_name in norm_lower:
                            ddi_drug_id = d_id
                            break

            if ddi_drug_id:
                mapped_count += 1
            self.db.add(
                MarketDrugProductIngredient(
                    market_product_id=product.id,
                    ingredient_name_raw=raw_name,
                    ingredient_name_normalized=normalized_name,
                    strength_raw=strength,
                    ddi_drug_id=ddi_drug_id,
                    mapping_confidence=100 if ddi_drug_id else None,
                    sort_order=idx,
                )
            )

        await self.db.flush()
        return mapped_count

    async def _to_list_item(self, product: MarketDrugProduct) -> MarketDrugProductListItem:
        ingredient_rows = (
            await self.db.execute(
                select(MarketDrugProductIngredient)
                .where(MarketDrugProductIngredient.market_product_id == product.id)
                .order_by(MarketDrugProductIngredient.sort_order.asc(), MarketDrugProductIngredient.id.asc())
            )
        ).scalars().all()
        ingredient_summary = [row.ingredient_name_raw for row in ingredient_rows]
        resolved_drug_ids = sorted({row.ddi_drug_id for row in ingredient_rows if row.ddi_drug_id})
        return MarketDrugProductListItem(
            id=product.id,
            registration_number=product.registration_number,
            product_name=product.product_name,
            normalized_product_name=product.normalized_product_name,
            dosage_form=product.dosage_form,
            packaging=product.packaging,
            route_name=product.route_name,
            is_expired=product.is_expired,
            is_withdrawn=product.is_withdrawn,
            image_url=product.image_url,
            ingredient_summary=ingredient_summary,
            resolved_drug_ids=resolved_drug_ids,
        )

    async def _to_detail_item(self, product: MarketDrugProduct) -> MarketDrugProductDetail:
        list_item = await self._to_list_item(product)
        return MarketDrugProductDetail(
            **list_item.model_dump(),
            source_product_id=product.source_product_id,
            old_registration_number=product.old_registration_number,
            quality_standard=product.quality_standard,
            shelf_life=product.shelf_life,
            decision_number=product.decision_number,
            issue_batch=product.issue_batch,
            registration_date=product.registration_date,
            expiry_date=product.expiry_date,
            raw_ingredients_text=product.raw_ingredients_text,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def _pick_demo_image(self, product: MarketDrugProduct) -> str:
        haystack = " ".join(
            filter(
                None,
                [
                    product.product_name,
                    product.normalized_product_name,
                    product.raw_ingredients_text,
                ],
            )
        ).lower()
        for term, image_url in IMAGE_MAP.items():
            if term in haystack:
                return image_url
        return "/static/market_drugs/tablet-box-blue.svg"
