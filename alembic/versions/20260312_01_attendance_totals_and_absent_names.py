"""attendance totals + absent names

Revision ID: 20260312_01
Revises: 20260222_02
Create Date: 2026-03-12 22:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260312_01"
down_revision: Union[str, Sequence[str], None] = "20260222_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attendance_fill",
        sa.Column("total_students", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "attendance_fill",
        sa.Column("present_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("attendance", sa.Column("absent_name", sa.String(), nullable=True))
    op.execute(
        "UPDATE attendance SET absent_name = students.full_name FROM students WHERE attendance.student_id = students.id"
    )
    op.alter_column("attendance", "absent_name", nullable=False)
    op.drop_constraint("uq_attendance_record", "attendance", type_="unique")
    op.drop_column("attendance", "student_id")
    op.create_index("ix_attendance_class_date", "attendance", ["class_id", "date"], unique=False)
    op.create_index("ix_attendance_fill_class_date", "attendance_fill", ["class_id", "date"], unique=False)


def downgrade() -> None:
    raise RuntimeError(
        "Irreversible migration: attendance.student_id cannot be restored from absent_name without data loss."
    )
