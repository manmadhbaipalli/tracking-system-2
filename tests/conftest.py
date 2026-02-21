"""Pytest fixtures and configuration."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db import Base, get_db
from app.main import app
from app.auth.models import User
from app.auth.service import hash_password


@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory SQLite database for testing.

    Yields:
        SQLAlchemy engine
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_db_engine):
    """Create a new database session for each test.

    Args:
        test_db_engine: Database engine from fixture

    Yields:
        Database session
    """
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = SessionLocal()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_db):
    """Create a FastAPI TestClient.

    Args:
        test_db: Database session fixture

    Returns:
        TestClient instance
    """
    return TestClient(app)


@pytest.fixture
def sample_user(test_db):
    """Create a sample user for testing.

    Args:
        test_db: Database session fixture

    Returns:
        Created User instance
    """
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user
