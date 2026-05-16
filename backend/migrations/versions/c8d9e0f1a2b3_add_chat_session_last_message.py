"""add_chat_session_last_message

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-05-16 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("last_message", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE chat_sessions AS cs
        SET last_message = lm.content
        FROM (
            SELECT DISTINCT ON (session_id) session_id, content
            FROM chat_messages
            ORDER BY session_id, created_at DESC, id DESC
        ) AS lm
        WHERE cs.id = lm.session_id
        """
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "last_message")
