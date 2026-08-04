"""
Database Connection
===================
SQLAlchemy engine, session factory, and FastAPI dependency for DB sessions.
Supports both SQLite (local dev) and PostgreSQL (production).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""
    pass


def _get_engine():
    """Create the SQLAlchemy engine based on DATABASE_URL."""
    settings = get_settings()
    url = settings.database_url

    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        url,
        connect_args=connect_args,
        echo=settings.debug,
        pool_pre_ping=True,
    )

    # Enable WAL mode for SQLite for better concurrency
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    return engine


engine = _get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a database session and ensures cleanup."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables. Called on application startup."""
    # Import models so they are registered on Base.metadata
    import app.database.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
