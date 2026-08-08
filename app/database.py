from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings


def get_database_url() -> str:
    """Get database URL from settings."""
    return get_settings().database_url


# Use SQLite for development if DATABASE_URL is SQLite
database_url = get_database_url()
if database_url.startswith("sqlite"):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
