"""add_health_baseline_and_notifications

Revision ID: e3dc80b5c221
Revises: 7ebd8c8081e3
Create Date: 2026-05-09 09:45:41.815438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3dc80b5c221'
down_revision: Union[str, Sequence[str], None] = '7ebd8c8081e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- user_health_baselines ---
    op.create_table(
        "user_health_baselines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("blood_type", sa.String(length=5), nullable=True),
        sa.Column("chronic_conditions", sa.Text(), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("current_medications", sa.Text(), nullable=True),
        sa.Column("is_pregnant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_breastfeeding", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "kidney_function",
            sa.Enum("normal", "mild_impairment", "moderate_impairment", "severe_impairment", name="kidneyfunction"),
            nullable=False,
            server_default="normal",
        ),
        sa.Column(
            "liver_function",
            sa.Enum("normal", "mild_impairment", "moderate_impairment", "severe_impairment", name="liverfunction"),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("health_goals", sa.Text(), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("onboarding_step", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_health_baselines_user_id", "user_health_baselines", ["user_id"])

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("medication_reminder", "health_alert", "system", "daily_summary", name="notificationtype"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "urgent", name="notificationpriority"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reminder_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reminder_id"], ["medication_reminders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_user_health_baselines_user_id", table_name="user_health_baselines")
    op.drop_table("user_health_baselines")
    op.execute("DROP TYPE IF EXISTS notificationpriority")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS liverfunction")
    op.execute("DROP TYPE IF EXISTS kidneyfunction")
