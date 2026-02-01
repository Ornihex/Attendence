# app/db.py
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def make_engine(url: str) -> Engine:
    """
    Примеры URL:
      SQLite:      sqlite:///./app.db
      PostgreSQL:  postgresql+psycopg://user:pass@localhost:5432/app
    """
    engine = create_engine(url, future=True)

    # В SQLite внешние ключи и каскады включаются отдельно:
    # https://www.sqlite.org/foreignkeys.html
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    return engine


def make_session_factory(engine: Engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)