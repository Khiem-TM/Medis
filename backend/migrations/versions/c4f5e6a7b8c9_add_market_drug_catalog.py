"""add_market_drug_catalog

Revision ID: c4f5e6a7b8c9
Revises: a92edf2cf810
Create Date: 2026-05-15 10:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c4f5e6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "a92edf2cf810"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


market_drug_source = postgresql.ENUM("dav", "manual", name="marketdrugsource", create_type=False)
market_drug_company_role = postgresql.ENUM("registrant", "manufacturer", name="marketdrugcompanyrole", create_type=False)
market_drug_document_type = postgresql.ENUM(
    "instruction",
    "label",
    "label_and_instruction",
    "quality_document",
    "decision",
    "other",
    name="marketdrugdocumenttype",
    create_type=False,
)
market_drug_image_type = postgresql.ENUM(
    "box_front",
    "box_back",
    "blister",
    "bottle",
    "strip",
    "unknown",
    name="marketdrugimagetype",
    create_type=False,
)
ingredient_mapping_status = postgresql.ENUM(
    "mapped",
    "pending",
    "rejected",
    name="ingredientmappingstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    market_drug_source.create(bind, checkfirst=True)
    market_drug_company_role.create(bind, checkfirst=True)
    market_drug_document_type.create(bind, checkfirst=True)
    market_drug_image_type.create(bind, checkfirst=True)
    ingredient_mapping_status.create(bind, checkfirst=True)

    op.create_table(
        "market_drug_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", market_drug_source, nullable=False),
        sa.Column("source_product_id", sa.Integer(), nullable=True),
        sa.Column("registration_number", sa.String(length=50), nullable=False),
        sa.Column("old_registration_number", sa.String(length=50), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_product_name", sa.String(length=255), nullable=True),
        sa.Column("dosage_form", sa.String(length=255), nullable=True),
        sa.Column("packaging", sa.Text(), nullable=True),
        sa.Column("route_name", sa.String(length=255), nullable=True),
        sa.Column("quality_standard", sa.String(length=100), nullable=True),
        sa.Column("shelf_life", sa.String(length=100), nullable=True),
        sa.Column("drug_type_name", sa.String(length=255), nullable=True),
        sa.Column("drug_type_id", sa.Integer(), nullable=True),
        sa.Column("drug_group_name", sa.String(length=255), nullable=True),
        sa.Column("drug_group_id", sa.Integer(), nullable=True),
        sa.Column("decision_number", sa.String(length=100), nullable=True),
        sa.Column("decision_url", sa.String(length=1000), nullable=True),
        sa.Column("issue_batch", sa.String(length=100), nullable=True),
        sa.Column("registration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("renewal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_expired", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_withdrawn", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_payload", sa.JSON(), nullable=True),
        sa.Column("source_payload_hash", sa.String(length=64), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "registration_number", name="uq_market_drug_products_source_registration"),
        sa.UniqueConstraint("source", "source_product_id", name="uq_market_drug_products_source_product"),
    )
    op.create_index("ix_market_drug_products_source", "market_drug_products", ["source"], unique=False)
    op.create_index("ix_market_drug_products_source_product_id", "market_drug_products", ["source_product_id"], unique=False)
    op.create_index("ix_market_drug_products_registration_number", "market_drug_products", ["registration_number"], unique=False)
    op.create_index("ix_market_drug_products_product_name", "market_drug_products", ["product_name"], unique=False)
    op.create_index("ix_market_drug_products_normalized_product_name", "market_drug_products", ["normalized_product_name"], unique=False)
    op.create_index("ix_market_drug_products_is_expired", "market_drug_products", ["is_expired"], unique=False)
    op.create_index("ix_market_drug_products_is_withdrawn", "market_drug_products", ["is_withdrawn"], unique=False)

    op.create_table(
        "drug_ingredients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_index("ix_drug_ingredients_canonical_name", "drug_ingredients", ["canonical_name"], unique=False)
    op.create_index("ix_drug_ingredients_normalized_name", "drug_ingredients", ["normalized_name"], unique=False)

    op.create_table(
        "drug_ingredient_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("alias_normalized", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["drug_ingredients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingredient_id", "alias", name="uq_drug_ingredient_aliases_ingredient_alias"),
    )
    op.create_index("ix_drug_ingredient_aliases_ingredient_id", "drug_ingredient_aliases", ["ingredient_id"], unique=False)
    op.create_index("ix_drug_ingredient_aliases_alias_normalized", "drug_ingredient_aliases", ["alias_normalized"], unique=False)

    op.create_table(
        "market_drug_product_ingredients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_product_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=True),
        sa.Column("ingredient_name_raw", sa.String(length=255), nullable=False),
        sa.Column("strength_raw", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["drug_ingredients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["market_product_id"], ["market_drug_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_drug_product_ingredients_market_product_id", "market_drug_product_ingredients", ["market_product_id"], unique=False)
    op.create_index("ix_market_drug_product_ingredients_ingredient_id", "market_drug_product_ingredients", ["ingredient_id"], unique=False)

    op.create_table(
        "ingredient_ddi_mappings",
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("ddi_drug_id", sa.String(length=50), nullable=False),
        sa.Column("mapping_status", ingredient_mapping_status, nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ddi_drug_id"], ["drugs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["drug_ingredients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ingredient_id", "ddi_drug_id"),
    )
    op.create_index("ix_ingredient_ddi_mappings_mapping_status", "ingredient_ddi_mappings", ["mapping_status"], unique=False)

    op.create_table(
        "market_drug_product_companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_product_id", sa.Integer(), nullable=False),
        sa.Column("company_role", market_drug_company_role, nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("country_code", sa.Integer(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_product_id"], ["market_drug_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_drug_product_companies_market_product_id", "market_drug_product_companies", ["market_product_id"], unique=False)
    op.create_index("ix_market_drug_product_companies_company_role", "market_drug_product_companies", ["company_role"], unique=False)

    op.create_table(
        "market_drug_product_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_product_id", sa.Integer(), nullable=False),
        sa.Column("document_type", market_drug_document_type, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("source", market_drug_source, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_product_id"], ["market_drug_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_drug_product_documents_market_product_id", "market_drug_product_documents", ["market_product_id"], unique=False)
    op.create_index("ix_market_drug_product_documents_document_type", "market_drug_product_documents", ["document_type"], unique=False)

    op.create_table(
        "market_drug_product_images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_product_id", sa.Integer(), nullable=False),
        sa.Column("image_type", market_drug_image_type, nullable=False),
        sa.Column("image_url", sa.String(length=1000), nullable=False),
        sa.Column("source", market_drug_source, nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_product_id"], ["market_drug_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_drug_product_images_market_product_id", "market_drug_product_images", ["market_product_id"], unique=False)
    op.create_index("ix_market_drug_product_images_image_type", "market_drug_product_images", ["image_type"], unique=False)

    op.add_column("prescription_items", sa.Column("market_product_id", sa.Integer(), nullable=True))
    op.create_index("ix_prescription_items_market_product_id", "prescription_items", ["market_product_id"], unique=False)
    op.create_foreign_key(
        "fk_prescription_items_market_product_id",
        "prescription_items",
        "market_drug_products",
        ["market_product_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_prescription_items_market_product_id", "prescription_items", type_="foreignkey")
    op.drop_index("ix_prescription_items_market_product_id", table_name="prescription_items")
    op.drop_column("prescription_items", "market_product_id")

    op.drop_index("ix_market_drug_product_images_image_type", table_name="market_drug_product_images")
    op.drop_index("ix_market_drug_product_images_market_product_id", table_name="market_drug_product_images")
    op.drop_table("market_drug_product_images")

    op.drop_index("ix_market_drug_product_documents_document_type", table_name="market_drug_product_documents")
    op.drop_index("ix_market_drug_product_documents_market_product_id", table_name="market_drug_product_documents")
    op.drop_table("market_drug_product_documents")

    op.drop_index("ix_market_drug_product_companies_company_role", table_name="market_drug_product_companies")
    op.drop_index("ix_market_drug_product_companies_market_product_id", table_name="market_drug_product_companies")
    op.drop_table("market_drug_product_companies")

    op.drop_index("ix_ingredient_ddi_mappings_mapping_status", table_name="ingredient_ddi_mappings")
    op.drop_table("ingredient_ddi_mappings")

    op.drop_index("ix_market_drug_product_ingredients_ingredient_id", table_name="market_drug_product_ingredients")
    op.drop_index("ix_market_drug_product_ingredients_market_product_id", table_name="market_drug_product_ingredients")
    op.drop_table("market_drug_product_ingredients")

    op.drop_index("ix_drug_ingredient_aliases_alias_normalized", table_name="drug_ingredient_aliases")
    op.drop_index("ix_drug_ingredient_aliases_ingredient_id", table_name="drug_ingredient_aliases")
    op.drop_table("drug_ingredient_aliases")

    op.drop_index("ix_drug_ingredients_normalized_name", table_name="drug_ingredients")
    op.drop_index("ix_drug_ingredients_canonical_name", table_name="drug_ingredients")
    op.drop_table("drug_ingredients")

    op.drop_index("ix_market_drug_products_is_withdrawn", table_name="market_drug_products")
    op.drop_index("ix_market_drug_products_is_expired", table_name="market_drug_products")
    op.drop_index("ix_market_drug_products_normalized_product_name", table_name="market_drug_products")
    op.drop_index("ix_market_drug_products_product_name", table_name="market_drug_products")
    op.drop_index("ix_market_drug_products_registration_number", table_name="market_drug_products")
    op.drop_index("ix_market_drug_products_source_product_id", table_name="market_drug_products")
    op.drop_index("ix_market_drug_products_source", table_name="market_drug_products")
    op.drop_table("market_drug_products")

    bind = op.get_bind()
    ingredient_mapping_status.drop(bind, checkfirst=True)
    market_drug_image_type.drop(bind, checkfirst=True)
    market_drug_document_type.drop(bind, checkfirst=True)
    market_drug_company_role.drop(bind, checkfirst=True)
    market_drug_source.drop(bind, checkfirst=True)
