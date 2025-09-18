#!/usr/bin/env python3
"""Initialize system management functionality."""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from open_agent.core.config import settings
from open_agent.db.database import Base, create_database_engine
from open_agent.db import database
from open_agent.db.init_system_data import init_system_data
from open_agent.models import *  # Import all models to ensure they're registered
from open_agent.utils.logger import get_logger

logger = get_logger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=database.engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise


def init_database():
    """Initialize database with system data."""
    logger.info("Initializing database with system data...")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
    db = SessionLocal()
    
    try:
        # Initialize system data
        init_system_data(db)
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection():
    """Check database connection."""
    logger.info("Checking database connection...")
    try:
        with database.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def main():
    """Main initialization function."""
    logger.info("Starting system initialization...")
    
    try:
        # Initialize database engine
        create_database_engine()
        
        # Check database connection
        if not check_database_connection():
            logger.error("Cannot connect to database. Please check your database configuration.")
            sys.exit(1)
        
        # Create tables
        create_tables()
        
        # Initialize system data
        init_database()
        
        logger.info("System initialization completed successfully!")
        print("\n✅ System initialization completed successfully!")
        print("\n📋 What was initialized:")
        print("   • Database tables for system management")
        print("   • Default permissions and roles")
        print("   • Default departments structure")
        print("   • System configuration")
        print("\n🚀 You can now start the application and access the system management features.")
        
    except Exception as e:
        logger.error(f"System initialization failed: {str(e)}")
        print(f"\n❌ System initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()