"""add promoted_by to users

Revision ID: 20260222_01
Revises: 20260221_01
Create Date: 2026-02-22 14:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260222_01"
down_revision: Union[str, Sequence[str], None] = "20260221_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("promoted_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_promoted_by_users",
        "users",
        "users",
        ["promoted_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_promoted_by_users", "users", type_="foreignkey")
    op.drop_column("users", "promoted_by")
