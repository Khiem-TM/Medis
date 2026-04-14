"""redesign_drug_tables

Thiết kế lại toàn bộ khu vực bảng thuốc theo ERD chuẩn hóa:
- drugs: generic_name, chemical_formula, molecular_formula; id mở rộng VARCHAR(50)
- drug_brand_names: thay drug_products, thêm image_url
- drug_dosage_forms: bảng 1-N mới
- drug_categories: bảng 1-N mới
- drug_atc_codes: bảng 1-N mới
- drug_interactions: cấu trúc mới (drug_id + interacts_with_id composite PK, không severity)
- drug_warnings: giữ cấu trúc, cập nhật FK length

Revision ID: a1b2c3d4e5f6
Revises: 066cf32d5b84
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '066cf32d5b84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────────────────
    # 1. Drop old child tables (có FK → drugs)
    # ──────────────────────────────────────────────────────────────────────────
    op.drop_index('ix_drug_warnings_drug_id', table_name='drug_warnings')
    op.drop_table('drug_warnings')

    op.drop_index('ix_drug_products_drug_id', table_name='drug_products')
    op.drop_table('drug_products')

    op.drop_table('drug_interactions')

    # Drop interactionseverity enum nếu tồn tại
    op.execute("DROP TYPE IF EXISTS interactionseverity")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Sửa bảng drugs
    # ──────────────────────────────────────────────────────────────────────────

    # Mở rộng id từ VARCHAR(10) → VARCHAR(50)
    # Cần đổi prescription_items.drug_id trước khi thay đổi FK (nullable, không FK rõ ràng)
    op.execute(
        "ALTER TABLE prescription_items ALTER COLUMN drug_id TYPE VARCHAR(50) USING drug_id::VARCHAR(50)"
    )
    op.execute(
        "ALTER TABLE drugs ALTER COLUMN id TYPE VARCHAR(50) USING id::VARCHAR(50)"
    )

    # Đổi tên cột name → generic_name
    op.alter_column('drugs', 'name', new_column_name='generic_name')

    # Mở rộng generic_name lên VARCHAR(255)
    op.execute(
        "ALTER TABLE drugs ALTER COLUMN generic_name TYPE VARCHAR(255) USING generic_name::VARCHAR(255)"
    )

    # Xóa cột không còn dùng
    op.drop_index('ix_drugs_atc_code', table_name='drugs')
    op.drop_column('drugs', 'atc_code')
    op.drop_column('drugs', 'dosage_form')
    op.drop_column('drugs', 'classification')
    op.drop_column('drugs', 'updated_at')

    # Thêm cột mới
    op.add_column('drugs', sa.Column('chemical_formula', sa.String(255), nullable=True))
    op.add_column('drugs', sa.Column('molecular_formula', sa.String(255), nullable=True))

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Tạo lại drug_warnings với FK trỏ đúng kích thước
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'drug_warnings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drug_id', sa.String(50), nullable=False),
        sa.Column('warning_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drug_warnings_drug_id', 'drug_warnings', ['drug_id'])

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Tạo bảng drug_brand_names (thay drug_products)
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'drug_brand_names',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drug_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('route', sa.String(255), nullable=True),
        sa.Column('strength', sa.String(255), nullable=True),
        sa.Column('dosage_form', sa.String(255), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drug_brand_names_drug_id', 'drug_brand_names', ['drug_id'])
    op.create_index('ix_drug_brand_names_name', 'drug_brand_names', ['name'])

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Tạo bảng drug_dosage_forms
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'drug_dosage_forms',
        sa.Column('drug_id', sa.String(50), nullable=False),
        sa.Column('dosage_form', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('drug_id', 'dosage_form'),
    )
    op.create_index('ix_drug_dosage_forms_drug_id', 'drug_dosage_forms', ['drug_id'])

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Tạo bảng drug_categories
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'drug_categories',
        sa.Column('drug_id', sa.String(50), nullable=False),
        sa.Column('category_name', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('drug_id', 'category_name'),
    )
    op.create_index('ix_drug_categories_drug_id', 'drug_categories', ['drug_id'])
    op.create_index('ix_drug_categories_name', 'drug_categories', ['category_name'])

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Tạo bảng drug_atc_codes
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'drug_atc_codes',
        sa.Column('drug_id', sa.String(50), nullable=False),
        sa.Column('atc_code', sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('drug_id', 'atc_code'),
    )
    op.create_index('ix_drug_atc_codes_drug_id', 'drug_atc_codes', ['drug_id'])
    op.create_index('ix_drug_atc_codes_code', 'drug_atc_codes', ['atc_code'])

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Tạo bảng drug_interactions (cấu trúc mới)
    # interacts_with_id KHÔNG có FK vì data nguồn có thể chứa ID chưa có trong DB
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'drug_interactions',
        sa.Column('drug_id', sa.String(50), nullable=False),
        sa.Column('interacts_with_id', sa.String(50), nullable=False),
        sa.Column('interacts_with_name', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('drug_id', 'interacts_with_id'),
    )
    op.create_index('ix_drug_interactions_drug_id', 'drug_interactions', ['drug_id'])
    op.create_index('ix_drug_interactions_with_id', 'drug_interactions', ['interacts_with_id'])


def downgrade() -> None:
    # Xóa các bảng mới
    op.drop_index('ix_drug_interactions_with_id', table_name='drug_interactions')
    op.drop_index('ix_drug_interactions_drug_id', table_name='drug_interactions')
    op.drop_table('drug_interactions')

    op.drop_index('ix_drug_atc_codes_code', table_name='drug_atc_codes')
    op.drop_index('ix_drug_atc_codes_drug_id', table_name='drug_atc_codes')
    op.drop_table('drug_atc_codes')

    op.drop_index('ix_drug_categories_name', table_name='drug_categories')
    op.drop_index('ix_drug_categories_drug_id', table_name='drug_categories')
    op.drop_table('drug_categories')

    op.drop_index('ix_drug_dosage_forms_drug_id', table_name='drug_dosage_forms')
    op.drop_table('drug_dosage_forms')

    op.drop_index('ix_drug_brand_names_name', table_name='drug_brand_names')
    op.drop_index('ix_drug_brand_names_drug_id', table_name='drug_brand_names')
    op.drop_table('drug_brand_names')

    op.drop_index('ix_drug_warnings_drug_id', table_name='drug_warnings')
    op.drop_table('drug_warnings')

    # Khôi phục drugs table (approximate — data sẽ bị mất)
    op.drop_column('drugs', 'molecular_formula')
    op.drop_column('drugs', 'chemical_formula')
    op.add_column('drugs', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('drugs', sa.Column('classification', sa.String(100), nullable=True))
    op.add_column('drugs', sa.Column('dosage_form', sa.String(50), nullable=True))
    op.add_column('drugs', sa.Column('atc_code', sa.String(20), nullable=True))
    op.create_index('ix_drugs_atc_code', 'drugs', ['atc_code'])
    op.alter_column('drugs', 'generic_name', new_column_name='name')
    op.execute("ALTER TABLE drugs ALTER COLUMN id TYPE VARCHAR(10) USING id::VARCHAR(10)")
    op.execute("ALTER TABLE prescription_items ALTER COLUMN drug_id TYPE VARCHAR(10) USING drug_id::VARCHAR(10)")

    # Khôi phục drug_warnings
    op.create_table(
        'drug_warnings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drug_id', sa.String(10), nullable=False),
        sa.Column('warning_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drug_warnings_drug_id', 'drug_warnings', ['drug_id'])

    # Khôi phục drug_products
    op.create_table(
        'drug_products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drug_id', sa.String(10), nullable=False),
        sa.Column('trade_name', sa.String(200), nullable=False),
        sa.Column('route', sa.String(100), nullable=False),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('formulation', sa.String(100), nullable=False),
        sa.Column('origin', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['drug_id'], ['drugs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drug_products_drug_id', 'drug_products', ['drug_id'])

    # Khôi phục drug_interactions (cũ)
    op.execute("CREATE TYPE interactionseverity AS ENUM ('minor', 'moderate', 'major')")
    op.create_table(
        'drug_interactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drug_id_1', sa.String(10), nullable=False),
        sa.Column('drug_id_2', sa.String(10), nullable=False),
        sa.Column('interaction_type', sa.String(100), nullable=True),
        sa.Column('severity', sa.Enum('minor', 'moderate', 'major', name='interactionseverity'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['drug_id_1'], ['drugs.id']),
        sa.ForeignKeyConstraint(['drug_id_2'], ['drugs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
