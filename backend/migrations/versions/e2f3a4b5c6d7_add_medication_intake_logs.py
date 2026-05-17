"""add_medication_intake_logs

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-16 20:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medication_intake_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reminder_id", sa.Integer(), nullable=True),
        sa.Column("prescription_item_id", sa.Integer(), nullable=True),
        sa.Column("drug_name", sa.String(200), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.Time(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "taken", "late", "missed", name="intakestatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["reminder_id"], ["medication_reminders.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["prescription_item_id"], ["prescription_items.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_medication_intake_logs_user_id", "medication_intake_logs", ["user_id"]
    )
    op.create_index(
        "ix_medication_intake_logs_reminder_id",
        "medication_intake_logs",
        ["reminder_id"],
    )
    op.create_index(
        "ix_medication_intake_logs_scheduled_date",
        "medication_intake_logs",
        ["scheduled_date"],
    )
    # One log per reminder per day (partial: only when reminder_id is set)
    op.create_index(
        "uq_intake_log_reminder_date",
        "medication_intake_logs",
        ["reminder_id", "scheduled_date"],
        unique=True,
        postgresql_where=sa.text("reminder_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_intake_log_reminder_date", table_name="medication_intake_logs")
    op.drop_index(
        "ix_medication_intake_logs_scheduled_date",
        table_name="medication_intake_logs",
    )
    op.drop_index(
        "ix_medication_intake_logs_reminder_id", table_name="medication_intake_logs"
    )
    op.drop_index(
        "ix_medication_intake_logs_user_id", table_name="medication_intake_logs"
    )
    op.drop_table("medication_intake_logs")
    op.execute("DROP TYPE IF EXISTS intakestatus")
