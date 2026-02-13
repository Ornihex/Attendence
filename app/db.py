from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import String, create_engine, ForeignKey, Enum, JSON
import enum
import os
import uuid
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('app/.env')

class Base(DeclarativeBase):
	pass

class TeacherBase(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class ClassBase(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    teacher_id: Mapped[str] = mapped_column(String, ForeignKey("teachers.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
class PupilBase(Base):
    __tablename__ = "pupils"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    class_id: Mapped[str] = mapped_column(String, ForeignKey("classes.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class AdminBase(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class AttendenceBase(Base):
    __tablename__ = "attendance"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id: Mapped[str] = mapped_column(String, ForeignKey("classes.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now)
    pupils: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    
        
    
    
    
    
POSTGRES_HOST = os.getenv("DB_HOST", 'db.com')
POSTGRES_PORT = os.getenv("DB_PORT", '5432')
POSTGRES_USERNAME = os.getenv("DB_USER", 'db_user')
POSTGRES_PASSWORD = os.getenv("DB_PASSWORD", 'password')
POSTGRES_DATABASE = os.getenv("DB_NAME", 'db_name')
DB_URL = f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}?sslmode=require&channel_binding=require'

engine = create_engine(DB_URL, echo=True)


def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)

create_db_and_tables()

