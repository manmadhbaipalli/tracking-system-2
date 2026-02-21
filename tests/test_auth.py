"""Tests for authentication module."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.auth.service import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    register_user,
    login_user,
)
from app.auth.models import User
from app.utils.exceptions import (
    ConflictError,
    AuthenticationError,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        hashed = hash_password("test_password")
        assert isinstance(hashed, str)
        assert hashed != "test_password"

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        hashed = hash_password("test_password")
        assert verify_password("wrong_password", hashed) is False


class TestTokenManagement:
    """Tests for token creation and verification."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a JWT string."""
        token = create_access_token(user_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self):
        """Test successful token verification."""
        user_id = 123
        token = create_access_token(user_id)
        decoded_user_id = verify_token(token)
        assert decoded_user_id == user_id

    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        with pytest.raises(AuthenticationError):
            verify_token("invalid_token")

    def test_verify_token_expired(self):
        """Test verification of expired token."""
        import jwt
        from app.config import settings
        from datetime import datetime, timedelta

        payload = {
            "user_id": 1,
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(AuthenticationError):
            verify_token(token)


class TestUserRegistration:
    """Tests for user registration."""

    def test_register_user_success(self, test_db: Session):
        """Test successful user registration."""
        email = "newuser@example.com"
        password = "secure_password"
        user = register_user(email, password, test_db)

        assert user.id is not None
        assert user.email == email
        assert user.hashed_password != password

    def test_register_user_duplicate_email(
        self,
        test_db: Session,
        sample_user: User,
    ):
        """Test registration with duplicate email."""
        with pytest.raises(ConflictError):
            register_user(sample_user.email, "password123", test_db)


class TestUserLogin:
    """Tests for user login."""

    def test_login_user_success(
        self,
        test_db: Session,
        sample_user: User,
    ):
        """Test successful user login."""
        user = login_user(sample_user.email, "password123", test_db)
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_login_user_invalid_email(self, test_db: Session):
        """Test login with invalid email."""
        with pytest.raises(AuthenticationError):
            login_user("nonexistent@example.com", "password", test_db)

    def test_login_user_invalid_password(
        self,
        test_db: Session,
        sample_user: User,
    ):
        """Test login with invalid password."""
        with pytest.raises(AuthenticationError):
            login_user(sample_user.email, "wrong_password", test_db)


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_register_endpoint_success(self, test_client: TestClient):
        """Test successful registration endpoint."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "secure_password",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_register_endpoint_duplicate(
        self,
        test_client: TestClient,
        sample_user: User,
    ):
        """Test registration with duplicate email."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": sample_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert "Email already registered" in data["detail"]

    def test_login_endpoint_success(
        self,
        test_client: TestClient,
        sample_user: User,
    ):
        """Test successful login endpoint."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_endpoint_invalid_credentials(
        self,
        test_client: TestClient,
        sample_user: User,
    ):
        """Test login with invalid credentials."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_user.email,
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]

    def test_register_endpoint_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email format."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    def test_login_endpoint_invalid_email(self, test_client: TestClient):
        """Test login with invalid email format."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert response.status_code == 422
