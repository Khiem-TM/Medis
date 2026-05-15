from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MarketDrugProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration_number: str
    product_name: str
    normalized_product_name: Optional[str] = None
    dosage_form: Optional[str] = None
    packaging: Optional[str] = None
    route_name: Optional[str] = None
    is_expired: bool
    is_withdrawn: bool
    image_url: Optional[str] = None
    ingredient_summary: list[str] = Field(default_factory=list)
    resolved_drug_ids: list[str] = Field(default_factory=list)


class MarketDrugProductDetail(MarketDrugProductListItem):
    model_config = ConfigDict(from_attributes=True)

    source_product_id: Optional[int] = None
    old_registration_number: Optional[str] = None
    quality_standard: Optional[str] = None
    shelf_life: Optional[str] = None
    decision_number: Optional[str] = None
    issue_batch: Optional[str] = None
    registration_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    raw_ingredients_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MarketDrugImportResult(BaseModel):
    imported_count: int
    updated_count: int
    mapped_ingredients: int
    imported_products: list[MarketDrugProductListItem]


class MarketInteractionCheckRequest(BaseModel):
    market_product_ids: list[int]

    @field_validator("market_product_ids")
    @classmethod
    def validate_ids(cls, v: list[int]) -> list[int]:
        if len(v) < 2:
            raise ValueError("Cần ít nhất 2 sản phẩm để kiểm tra tương tác")
        if len(v) > 10:
            raise ValueError("Tối đa 10 sản phẩm mỗi lần kiểm tra")
        if len(v) != len(set(v)):
            raise ValueError("Danh sách sản phẩm không được trùng lặp")
        return v


class ProductIngredientInfo(BaseModel):
    product_id: int
    product_name: str
    ddi_drug_ids: list[str]


class MarketInteractionCheckResult(BaseModel):
    products: list[ProductIngredientInfo]
    unmapped_products: list[int]
    ddi_result: Optional[dict] = None
