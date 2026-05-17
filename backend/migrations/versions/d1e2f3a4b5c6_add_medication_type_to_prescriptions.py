"""add_medication_type_to_prescriptions

Revision ID: d1e2f3a4b5c6
Revises: c8d9e0f1a2b3
Create Date: 2026-05-16 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE medicationtype AS ENUM ('chronic', 'periodic')")
    op.add_column(
        "prescriptions",
        sa.Column(
            "medication_type",
            sa.Enum("chronic", "periodic", name="medicationtype"),
            nullable=False,
            server_default="periodic",
        ),
    )
    op.add_column("prescriptions", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("prescriptions", sa.Column("end_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("prescriptions", "end_date")
    op.drop_column("prescriptions", "start_date")
    op.drop_column("prescriptions", "medication_type")
    op.execute("DROP TYPE IF EXISTS medicationtype")
