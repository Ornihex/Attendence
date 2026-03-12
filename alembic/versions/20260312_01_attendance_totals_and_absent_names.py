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


def downgrade() -> None:
    op.add_column("attendance", sa.Column("student_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "attendance_student_id_fkey",
        "attendance",
        "students",
        ["student_id"],
        ["id"],
    )
    op.create_unique_constraint("uq_attendance_record", "attendance", ["date", "class_id", "student_id"])
    op.drop_column("attendance", "absent_name")
    op.drop_column("attendance_fill", "present_count")
    op.drop_column("attendance_fill", "total_students")
