from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user
from app.database import get_db
from app.models.user import User
from app.redis_client import get_redis
from app.schemas.market_drug import (
    MarketDrugImportResult,
    MarketDrugProductDetail,
    MarketInteractionCheckRequest,
    MarketInteractionCheckResult,
)
from app.services.market_drug_service import MarketDrugService

router = APIRouter(prefix="/market-drugs", tags=["🏪 Thuốc thị trường"])
admin_router = APIRouter(prefix="/admin/market-drugs", tags=["🔧 Admin Market Drugs"])


@router.get("", summary="Danh sách thuốc thị trường từ DAV")
async def list_market_drugs(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=100),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await MarketDrugService(db).search_products(page, size, search)


@router.post(
    "/check-interactions",
    response_model=MarketInteractionCheckResult,
    summary="Kiểm tra tương tác giữa các thuốc thị trường (map sang DDI layer)",
)
async def check_market_interactions(
    body: MarketInteractionCheckRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: User = Depends(get_current_user),
):
    return await MarketDrugService(db).check_market_product_interactions(
        body.market_product_ids, redis
    )


@router.get(
    "/check-interactions",
    response_model=MarketInteractionCheckResult,
    summary="Kiểm tra tương tác giữa các thuốc thị trường qua query params",
)
async def check_market_interactions_get(
    market_product_ids: list[int] = Query(..., description="Danh sách market product id"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: User = Depends(get_current_user),
):
    return await MarketDrugService(db).check_market_product_interactions(
        market_product_ids, redis
    )


@router.get("/{product_id:int}", response_model=MarketDrugProductDetail, summary="Chi tiết thuốc thị trường")
async def get_market_drug(product_id: int, db: AsyncSession = Depends(get_db)):
    return await MarketDrugService(db).get_product_by_id(product_id)


@admin_router.post(
    "/import-demo",
    response_model=MarketDrugImportResult,
    status_code=status.HTTP_201_CREATED,
    summary="Import một lượng nhỏ thuốc DAV phục vụ test",
)
async def import_demo_market_drugs(
    limit_per_term: int = Query(2, ge=1, le=5),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await MarketDrugService(db).import_demo_products(limit_per_term=limit_per_term)
