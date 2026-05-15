"""simplify_market_drug_catalog

Revision ID: f6a7b8c9d0e1
Revises: c4f5e6a7b8c9
Create Date: 2026-05-15 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "c4f5e6a7b8c9"
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
    op.add_column("market_drug_products", sa.Column("raw_ingredients_text", sa.Text(), nullable=True))
    op.add_column("market_drug_products", sa.Column("image_url", sa.String(length=1000), nullable=True))

    op.add_column("market_drug_product_ingredients", sa.Column("ingredient_name_normalized", sa.String(length=255), nullable=True))
    op.add_column("market_drug_product_ingredients", sa.Column("ddi_drug_id", sa.String(length=50), nullable=True))
    op.add_column("market_drug_product_ingredients", sa.Column("mapping_confidence", sa.Integer(), nullable=True))
    op.create_index(
        "ix_market_drug_product_ingredients_ingredient_name_normalized",
        "market_drug_product_ingredients",
        ["ingredient_name_normalized"],
        unique=False,
    )
    op.create_index(
        "ix_market_drug_product_ingredients_ddi_drug_id",
        "market_drug_product_ingredients",
        ["ddi_drug_id"],
        unique=False,
    )
    op.create_foreign_key(
        "market_drug_product_ingredients_ddi_drug_id_fkey",
        "market_drug_product_ingredients",
        "drugs",
        ["ddi_drug_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        UPDATE market_drug_products
        SET raw_ingredients_text = COALESCE(
            source_payload->'thongTinThuocCoBan'->>'hoatChatChinh',
            source_payload->>'hoatChatChinh'
        )
        WHERE raw_ingredients_text IS NULL
        """
    )
    op.execute(
        """
        UPDATE market_drug_products AS p
        SET image_url = img.image_url
        FROM (
            SELECT DISTINCT ON (market_product_id)
                market_product_id,
                image_url
            FROM market_drug_product_images
            ORDER BY market_product_id, is_primary DESC, sort_order ASC, id ASC
        ) AS img
        WHERE p.id = img.market_product_id
          AND p.image_url IS NULL
        """
    )
    op.execute(
        """
        UPDATE market_drug_product_ingredients AS mpi
        SET ingredient_name_normalized = di.normalized_name
        FROM drug_ingredients AS di
        WHERE mpi.ingredient_id = di.id
          AND mpi.ingredient_name_normalized IS NULL
        """
    )
    op.execute(
        """
        UPDATE market_drug_product_ingredients
        SET ingredient_name_normalized = lower(ingredient_name_raw)
        WHERE ingredient_name_normalized IS NULL
        """
    )
    op.execute(
        """
        UPDATE market_drug_product_ingredients AS mpi
        SET ddi_drug_id = idm.ddi_drug_id,
            mapping_confidence = idm.confidence
        FROM ingredient_ddi_mappings AS idm
        WHERE mpi.ingredient_id = idm.ingredient_id
          AND mpi.ddi_drug_id IS NULL
        """
    )

    op.drop_constraint("uq_market_drug_products_source_product", "market_drug_products", type_="unique")
    op.drop_constraint("uq_market_drug_products_source_registration", "market_drug_products", type_="unique")
    op.drop_index("ix_market_drug_products_source", table_name="market_drug_products")
    op.create_unique_constraint(
        "uq_market_drug_products_source_product_id",
        "market_drug_products",
        ["source_product_id"],
    )
    op.create_unique_constraint(
        "uq_market_drug_products_registration_number",
        "market_drug_products",
        ["registration_number"],
    )

    op.drop_column("market_drug_products", "source")
    op.drop_column("market_drug_products", "drug_type_name")
    op.drop_column("market_drug_products", "drug_type_id")
    op.drop_column("market_drug_products", "drug_group_name")
    op.drop_column("market_drug_products", "drug_group_id")
    op.drop_column("market_drug_products", "decision_url")
    op.drop_column("market_drug_products", "renewal_date")

    op.drop_constraint(
        "market_drug_product_ingredients_ingredient_id_fkey",
        "market_drug_product_ingredients",
        type_="foreignkey",
    )
    op.drop_index("ix_market_drug_product_ingredients_ingredient_id", table_name="market_drug_product_ingredients")
    op.drop_column("market_drug_product_ingredients", "ingredient_id")
    op.create_unique_constraint(
        "uq_market_drug_product_ingredients_product_ingredient",
        "market_drug_product_ingredients",
        ["market_product_id", "ingredient_name_normalized", "strength_raw"],
    )

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

    op.drop_index("ix_drug_ingredient_aliases_alias_normalized", table_name="drug_ingredient_aliases")
    op.drop_index("ix_drug_ingredient_aliases_ingredient_id", table_name="drug_ingredient_aliases")
    op.drop_table("drug_ingredient_aliases")

    op.drop_index("ix_drug_ingredients_normalized_name", table_name="drug_ingredients")
    op.drop_index("ix_drug_ingredients_canonical_name", table_name="drug_ingredients")
    op.drop_table("drug_ingredients")

    op.execute("DROP TYPE IF EXISTS ingredientmappingstatus")
    op.execute("DROP TYPE IF EXISTS marketdrugimagetype")
    op.execute("DROP TYPE IF EXISTS marketdrugdocumenttype")
    op.execute("DROP TYPE IF EXISTS marketdrugcompanyrole")
    op.execute("DROP TYPE IF EXISTS marketdrugsource")


def downgrade() -> None:
    bind = op.get_bind()
    market_drug_source.create(bind, checkfirst=True)
    market_drug_company_role.create(bind, checkfirst=True)
    market_drug_document_type.create(bind, checkfirst=True)
    market_drug_image_type.create(bind, checkfirst=True)
    ingredient_mapping_status.create(bind, checkfirst=True)

    op.add_column("market_drug_products", sa.Column("source", market_drug_source, nullable=True))
    op.add_column("market_drug_products", sa.Column("drug_type_name", sa.String(length=255), nullable=True))
    op.add_column("market_drug_products", sa.Column("drug_type_id", sa.Integer(), nullable=True))
    op.add_column("market_drug_products", sa.Column("drug_group_name", sa.String(length=255), nullable=True))
    op.add_column("market_drug_products", sa.Column("drug_group_id", sa.Integer(), nullable=True))
    op.add_column("market_drug_products", sa.Column("decision_url", sa.String(length=1000), nullable=True))
    op.add_column("market_drug_products", sa.Column("renewal_date", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE market_drug_products SET source = 'dav' WHERE source IS NULL")
    op.alter_column("market_drug_products", "source", nullable=False)

    op.drop_constraint("uq_market_drug_products_source_product_id", "market_drug_products", type_="unique")
    op.drop_constraint("uq_market_drug_products_registration_number", "market_drug_products", type_="unique")
    op.create_index("ix_market_drug_products_source", "market_drug_products", ["source"], unique=False)
    op.create_unique_constraint(
        "uq_market_drug_products_source_product",
        "market_drug_products",
        ["source", "source_product_id"],
    )
    op.create_unique_constraint(
        "uq_market_drug_products_source_registration",
        "market_drug_products",
        ["source", "registration_number"],
    )

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

    op.drop_constraint(
        "uq_market_drug_product_ingredients_product_ingredient",
        "market_drug_product_ingredients",
        type_="unique",
    )
    op.drop_constraint(
        "market_drug_product_ingredients_ddi_drug_id_fkey",
        "market_drug_product_ingredients",
        type_="foreignkey",
    )
    op.drop_index("ix_market_drug_product_ingredients_ddi_drug_id", table_name="market_drug_product_ingredients")
    op.drop_index("ix_market_drug_product_ingredients_ingredient_name_normalized", table_name="market_drug_product_ingredients")
    op.add_column("market_drug_product_ingredients", sa.Column("ingredient_id", sa.Integer(), nullable=True))
    op.create_index("ix_market_drug_product_ingredients_ingredient_id", "market_drug_product_ingredients", ["ingredient_id"], unique=False)
    op.create_foreign_key(
        "market_drug_product_ingredients_ingredient_id_fkey",
        "market_drug_product_ingredients",
        "drug_ingredients",
        ["ingredient_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("market_drug_product_ingredients", "mapping_confidence")
    op.drop_column("market_drug_product_ingredients", "ddi_drug_id")
    op.drop_column("market_drug_product_ingredients", "ingredient_name_normalized")

    op.drop_column("market_drug_products", "image_url")
    op.drop_column("market_drug_products", "raw_ingredients_text")
