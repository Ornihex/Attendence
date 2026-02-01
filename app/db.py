from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import String, create_engine, ForeignKey, Enum, JSON
import enum
import os
import uuid
import bcrypt
from datetime import datetime

class Base(DeclarativeBase):
	pass

class Class(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    
    
    
    
    
POSTGRES_HOST = os.getenv("DB_HOST", 'ep-polished-term-ah310ruc-pooler.c-3.us-east-1.aws.neon.tech')
POSTGRES_PORT = os.getenv("DB_PORT", '5432')
POSTGRES_USERNAME = os.getenv("DB_USER", 'neondb_owner')
POSTGRES_PASSWORD = os.getenv("DB_PASSWORD", 'npg_Qzf1jFDsJc6P')
POSTGRES_DATABASE = os.getenv("DB_NAME", 'neondb')
DB_URL = f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}?sslmode=require&channel_binding=require'

engine = create_engine(DB_URL, echo=True)


def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)

create_db_and_tables()

