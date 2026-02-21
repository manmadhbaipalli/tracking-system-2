"""
Claims Service Platform - Database Configuration

SQLAlchemy setup with connection pooling, session management, and encrypted field support.
"""

from sqlalchemy import create_engine, MetaData, TypeDecorator, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import contextlib

from app.core.config import settings, get_database_url
from app.utils.encryption import encrypt_field, decrypt_field

# Database engine with connection pooling
engine = create_engine(
    get_database_url(),
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=300,  # 5 minutes
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()

# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

Base.metadata = MetaData(naming_convention=convention)


class EncryptedString(TypeDecorator):
    """Custom SQLAlchemy type for encrypted string fields (SSN, TIN, etc.)"""
    impl = String
    cache_ok = True

    def __init__(self, length=None, **kwargs):
        self.length = length
        super().__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database"""
        if value is not None:
            return encrypt_field(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt value when retrieving from database"""
        if value is not None:
            return decrypt_field(value)
        return value

    def load_dialect_impl(self, dialect):
        """Load appropriate dialect implementation"""
        if self.length:
            return dialect.type_descriptor(String(self.length))
        return dialect.type_descriptor(Text())


class EncryptedText(TypeDecorator):
    """Custom SQLAlchemy type for encrypted text fields (payment info, etc.)"""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database"""
        if value is not None:
            return encrypt_field(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt value when retrieving from database"""
        if value is not None:
            return decrypt_field(value)
        return value


# Database session dependency
def get_db() -> Generator[Session, None, None]:
    """
    Database session generator for FastAPI dependency injection

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextlib.contextmanager
def get_db_context():
    """
    Database session context manager for service layer

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Database initialization and health check
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    Check if database connection is healthy

    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False


# Database utilities
def drop_all_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)


def create_all_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


# Transaction helpers
class DatabaseTransaction:
    """Database transaction context manager"""

    def __init__(self, db: Session):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.db.commit()
        else:
            self.db.rollback()


def with_transaction(db: Session):
    """Create a transaction context manager"""
    return DatabaseTransaction(db)