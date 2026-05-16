"""add_chat_sessions

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f7
Create Date: 2026-05-16 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("ix_chat_sessions_last_message_at", "chat_sessions", ["last_message_at"])

    op.add_column("chat_messages", sa.Column("session_id", sa.Integer(), nullable=True))
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_foreign_key(
        "fk_chat_messages_session_id_chat_sessions",
        "chat_messages",
        "chat_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        """
        INSERT INTO chat_sessions (user_id, title, created_at, updated_at, last_message_at)
        SELECT
            user_id,
            'Cuộc trò chuyện trước đây',
            MIN(created_at),
            MAX(created_at),
            MAX(created_at)
        FROM chat_messages
        GROUP BY user_id
        """
    )
    op.execute(
        """
        UPDATE chat_messages AS cm
        SET session_id = cs.id
        FROM chat_sessions AS cs
        WHERE cm.user_id = cs.user_id
          AND cs.title = 'Cuộc trò chuyện trước đây'
          AND cm.session_id IS NULL
        """
    )
    op.alter_column("chat_messages", "session_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_chat_messages_session_id_chat_sessions", "chat_messages", type_="foreignkey")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_column("chat_messages", "session_id")
    op.drop_index("ix_chat_sessions_last_message_at", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
