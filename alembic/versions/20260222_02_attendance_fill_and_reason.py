"""add attendance fill + reason

Revision ID: 20260222_02
Revises: 20260222_01
Create Date: 2026-02-22 15:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260222_02"
down_revision: Union[str, Sequence[str], None] = "20260222_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attendance", sa.Column("reason", sa.String(), nullable=True))
    op.create_table(
        "attendance_fill",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("filled_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("date", "class_id", name="uq_attendance_fill"),
    )


def downgrade() -> None:
    op.drop_table("attendance_fill")
    op.drop_column("attendance", "reason")
