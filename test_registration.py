#!/usr/bin/env python3
"""Simple test script to debug registration issues."""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.auth import AuthService
from app.schemas.user import UserCreate
from app.core.config import settings

# Create a test database session
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_registration():
    """Test user registration directly."""
    db = SessionLocal()
    try:
        # Create test user data
        user_data = UserCreate(
            email="debug@example.com",
            password="testpassword123"
        )

        print("Testing user registration...")
        print(f"Email: {user_data.email}")
        print(f"Password length: {len(user_data.password)}")

        # Attempt registration
        user = await AuthService.register_user(db, user_data)
        print(f"Registration successful! User ID: {user.id}")

    except Exception as e:
        print(f"Registration failed with error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_registration())