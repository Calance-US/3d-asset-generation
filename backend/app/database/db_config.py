"""Database configuration."""

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

# Set up logging
logger = logging.getLogger(__name__)

url = make_url(settings.DATABASE_URL)

# For SQLite, do not set pool_size, max_overflow, pool_timeout, pool_recycle
if url.get_backend_name() == "sqlite":
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False}
        if settings.ENVIRONMENT == "development"
        else {},
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=20,
        max_overflow=30,
        pool_timeout=60,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with proper error handling and logging."""
    try:
        # Environment-specific initialization
        if settings.ENVIRONMENT == "development":
            logger.info("Initializing database in development mode...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
        elif settings.ENVIRONMENT == "testing":
            logger.info("Initializing database in testing mode...")
            Base.metadata.drop_all(bind=engine)  # Clean slate for tests
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized for testing")
        else:  # production or other environments
            logger.warning(
                f"Database initialization skipped in {settings.ENVIRONMENT} environment. "
                "Please use migrations for database changes."
            )
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        raise
