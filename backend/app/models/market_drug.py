from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.drug import Drug
    from app.models.prescription import PrescriptionItem


class MarketDrugProduct(Base):
    __tablename__ = "market_drug_products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True, index=True)
    registration_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    old_registration_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    dosage_form: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    packaging: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    route_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quality_standard: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shelf_life: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decision_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issue_batch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    registration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    is_withdrawn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    raw_ingredients_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_payload_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    ingredients: Mapped[list["MarketDrugProductIngredient"]] = relationship(
        back_populates="market_product",
        cascade="all, delete-orphan",
    )
    prescription_items: Mapped[list["PrescriptionItem"]] = relationship(
        back_populates="market_product",
    )


class MarketDrugProductIngredient(Base):
    __tablename__ = "market_drug_product_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_product_id: Mapped[int] = mapped_column(
        ForeignKey("market_drug_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name_raw: Mapped[str] = mapped_column(String(255), nullable=False)
    ingredient_name_normalized: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    strength_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ddi_drug_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("drugs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    mapping_confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "market_product_id",
            "ingredient_name_normalized",
            "strength_raw",
            name="uq_market_drug_product_ingredients_product_ingredient",
        ),
    )

    market_product: Mapped["MarketDrugProduct"] = relationship(back_populates="ingredients")
    ddi_drug: Mapped[Optional["Drug"]] = relationship()
