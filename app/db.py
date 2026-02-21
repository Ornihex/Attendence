from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import String, Integer, Boolean, Date, create_engine, ForeignKey, Enum, UniqueConstraint
import enum
import os
import bcrypt
from datetime import date, datetime
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError, ProgrammingError

load_dotenv('app/.env')

class Base(DeclarativeBase):
    pass


class RoleEnum(str, enum.Enum):
    teacher = "teacher"
    admin = "admin"


class AttendanceStatusEnum(str, enum.Enum):
    present = "present"
    excused = "excused"
    unexcused = "unexcused"


class UserBase(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class ClassBase(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    

class StudentBase(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class AttendanceBase(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    status: Mapped[AttendanceStatusEnum] = mapped_column(Enum(AttendanceStatusEnum), nullable=False)
    __table_args__ = (UniqueConstraint("date", "class_id", "student_id", name="uq_attendance_record"),)


POSTGRES_HOST = os.getenv("DB_HOST", 'db.com')
POSTGRES_PORT = os.getenv("DB_PORT", '5432')
POSTGRES_USERNAME = os.getenv("DB_USER", 'db_user')
POSTGRES_PASSWORD = os.getenv("DB_PASSWORD", 'password')
POSTGRES_DATABASE = os.getenv("DB_NAME", 'db_name')
DB_URL = f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}?sslmode=require&channel_binding=require'

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(engine)


def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)


def seed_default_admin() -> None:
    admin_login = os.getenv("ADMIN_LOGIN", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    try:
        with SessionLocal() as s:
            existing = s.query(UserBase).filter(UserBase.login == admin_login).first()
            if existing:
                return
            hashed = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user = UserBase(login=admin_login, password=hashed, role=RoleEnum.admin)
            s.add(user)
            s.commit()
    except (OperationalError, ProgrammingError):
        # Tables may not exist yet before Alembic migration.
        return

