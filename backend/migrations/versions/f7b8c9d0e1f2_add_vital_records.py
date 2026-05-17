"""add vital_records table

Revision ID: f7b8c9d0e1f2
Revises: e2f3a4b5c6d7
Create Date: 2026-05-17

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "f7b8c9d0e1f2"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vital_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("systolic_bp", sa.Integer(), nullable=True),
        sa.Column("diastolic_bp", sa.Integer(), nullable=True),
        sa.Column("blood_glucose", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vital_records_user_id", "vital_records", ["user_id"])
    op.create_index("ix_vital_records_recorded_at", "vital_records", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_vital_records_recorded_at", table_name="vital_records")
    op.drop_index("ix_vital_records_user_id", table_name="vital_records")
    op.drop_table("vital_records")
