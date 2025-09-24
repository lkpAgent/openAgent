"""Database connection and session management."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from ..core.config import get_settings
from .base import Base


# Global variables
engine = None
SessionLocal = None


def create_database_engine():
    """Create database engine."""
    global engine, SessionLocal
    
    settings = get_settings()
    database_url = settings.database.url
    
    # Validate that we're using PostgreSQL
    if not database_url.startswith("postgresql"):
        raise ValueError("Only PostgreSQL databases are supported. Please update your DATABASE_URL.")
    
    # Engine configuration for PostgreSQL
    engine_kwargs = {
        "echo": settings.database.echo,
        "pool_size": settings.database.pool_size,
        "max_overflow": settings.database.max_overflow,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    
    engine = create_engine(database_url, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logging.info(f"PostgreSQL database engine created: {database_url}")


async def init_db():
    """Initialize database."""
    global engine
    
    if engine is None:
        create_database_engine()
    
    # Import all models to ensure they are registered
    from ..models import user, conversation, message, knowledge_base, \
        department, user_department, permission
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created")


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    global SessionLocal
    
    if SessionLocal is None:
        create_database_engine()
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logging.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session (synchronous)."""
    global SessionLocal
    
    if SessionLocal is None:
        create_database_engine()
    
    return SessionLocal()