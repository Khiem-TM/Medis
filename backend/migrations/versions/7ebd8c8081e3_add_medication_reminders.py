"""add_medication_reminders

Revision ID: 7ebd8c8081e3
Revises: a1b2c3d4e5f6
Create Date: 2026-04-23 14:54:27.810525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ebd8c8081e3'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'medication_reminders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prescription_item_id', sa.Integer(), nullable=True),
        sa.Column('drug_name', sa.String(length=200), nullable=False),
        sa.Column('reminder_time', sa.Time(), nullable=False),
        sa.Column('frequency', sa.String(length=50), nullable=False),
        sa.Column('days_of_week', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prescription_item_id'], ['prescription_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_medication_reminders_user_id', 'medication_reminders', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_medication_reminders_user_id', table_name='medication_reminders')
    op.drop_table('medication_reminders')
