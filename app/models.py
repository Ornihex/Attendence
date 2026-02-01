# app/models.py
from __future__ import annotations

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Важно для Alembic: стабильные имена constraints/indexes
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)

    # например, школьный идентификатор/СНИЛС/что угодно внешнее
    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Teacher(Base, TimestampMixin):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    lessons: Mapped[list["Lesson"]] = relationship(back_populates="teacher")


class ClassGroup(Base, TimestampMixin):
    """
    Класс/группа, например "7А", "10Б", "5-1 (математика)".
    """
    __tablename__ = "class_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)   # "7А"
    year: Mapped[int] = mapped_column(Integer, nullable=False)      # учебный год старта, например 2025
    grade: Mapped[int] = mapped_column(Integer, nullable=False)     # 1..11

    curator_teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    curator: Mapped[Optional[Teacher]] = relationship()

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="class_group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="class_group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # минимальная защита от дублей типа два "7А" в одном учебном году
        UniqueConstraint("name", "year", name="uq_class_groups_name_year"),
        CheckConstraint("grade >= 1 AND grade <= 11", name="grade_range"),
    )


class Enrollment(Base, TimestampMixin):
    """
    Прикрепление ученика к классу на период.
    Важно хранить историю переходов.
    """
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_group_id: Mapped[int] = mapped_column(
        ForeignKey("class_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    student: Mapped[Student] = relationship(back_populates="enrollments")
    class_group: Mapped[ClassGroup] = relationship(back_populates="enrollments")

    __table_args__ = (
        # один и тот же ученик не должен иметь два "одинаковых" вступления в один класс в одну дату
        UniqueConstraint(
            "student_id", "class_group_id", "start_date",
            name="uq_enrollments_student_class_start",
        ),
        Index("ix_enrollments_class_group_id", "class_group_id"),
        Index("ix_enrollments_student_id", "student_id"),
    )


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    class_group_id: Mapped[int] = mapped_column(
        ForeignKey("class_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    room: Mapped[Optional[str]] = mapped_column(String(50))
    topic: Mapped[Optional[str]] = mapped_column(String(255))

    class_group: Mapped[ClassGroup] = relationship(back_populates="lessons")
    subject: Mapped[Subject] = relationship()
    teacher: Mapped[Optional[Teacher]] = relationship(back_populates="lessons")

    attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_lessons_class_group_starts_at", "class_group_id", "starts_at"),
    )


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(
            AttendanceStatus,
            native_enum=False,      # важно для переносимости SQLite <-> Postgres
            create_constraint=True, # создаст CHECK в SQLite
            length=16,
        ),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(Text)  # причина/комментарий
    marked_by_teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,  # в UTC; для Postgres обычно тоже удобно
    )

    lesson: Mapped[Lesson] = relationship(back_populates="attendance")
    student: Mapped[Student] = relationship(back_populates="attendance")
    marked_by: Mapped[Optional[Teacher]] = relationship()

    __table_args__ = (
        # ключевое правило: 1 отметка на ученика в рамках урока
        UniqueConstraint("lesson_id", "student_id", name="uq_attendance_lesson_student"),
        Index("ix_attendance_student_id", "student_id"),
        Index("ix_attendance_lesson_id", "lesson_id"),
    )