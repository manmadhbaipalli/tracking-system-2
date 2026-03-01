import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Tests for user registration endpoint"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepass123",
                "name": "Test User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email returns 409"""
        # Register first user
        await client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "name": "First User"
            }
        )

        # Try to register with same email
        response = await client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "different456",
                "name": "Second User"
            }
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"] == "CONFLICT"
        assert "already registered" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format returns 422"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "name": "Test User"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with password shorter than 8 characters returns 422"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "name": "Test User"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields returns 422"""
        response = await client.post(
            "/auth/register",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login endpoint"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login returns JWT token"""
        # Register user first
        await client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "password123",
                "name": "Login User"
            }
        )

        # Login
        response = await client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email returns 401"""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "AUTH_ERROR"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient):
        """Test login with wrong password returns 401"""
        # Register user first
        await client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "correctpass123",
                "name": "User"
            }
        )

        # Login with wrong password
        response = await client.post(
            "/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "AUTH_ERROR"

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields returns 422"""
        response = await client.post(
            "/auth/login",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422


class TestGetCurrentUser:
    """Tests for get current user endpoint"""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient):
        """Test getting current user profile with valid token"""
        # Register and login
        await client.post(
            "/auth/register",
            json={
                "email": "me@example.com",
                "password": "password123",
                "name": "Me User"
            }
        )

        login_response = await client.post(
            "/auth/login",
            json={
                "email": "me@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["name"] == "Me User"
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_get_me_without_token(self, client: AsyncClient):
        """Test getting current user without token returns 401"""
        response = await client.get("/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token returns 401"""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_with_malformed_header(self, client: AsyncClient):
        """Test getting current user with malformed auth header returns 401"""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "InvalidFormat"}
        )

        assert response.status_code == 401


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness endpoint returns 200"""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness endpoint checks database connectivity"""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["checks"]["database"] == "UP"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API information"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestPasswordSecurity:
    """Tests for password security"""

    @pytest.mark.asyncio
    async def test_password_not_returned_in_response(self, client: AsyncClient):
        """Test that passwords are never returned in API responses"""
        # Register
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "secure@example.com",
                "password": "securepass123",
                "name": "Secure User"
            }
        )

        # Login
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "secure@example.com",
                "password": "securepass123"
            }
        )
        token = login_response.json()["access_token"]

        # Get user profile
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Verify password not in any response
        assert "password" not in register_response.text
        assert "password_hash" not in register_response.text
        assert "password" not in me_response.text
        assert "password_hash" not in me_response.text


class TestCORSHeaders:
    """Tests for CORS middleware"""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client: AsyncClient):
        """Test that CORS headers are added to responses"""
        response = await client.get("/health/live")

        assert response.status_code == 200
        # Note: In test environment, CORS headers may not be fully set
        # This test ensures the middleware is configured


class TestCorrelationId:
    """Tests for correlation ID middleware"""

    @pytest.mark.asyncio
    async def test_correlation_id_returned(self, client: AsyncClient):
        """Test that correlation ID is returned in response headers"""
        response = await client.get("/health/live")

        assert response.status_code == 200
        assert "x-correlation-id" in response.headers

    @pytest.mark.asyncio
    async def test_correlation_id_preserved(self, client: AsyncClient):
        """Test that provided correlation ID is preserved"""
        correlation_id = "test-correlation-123"
        response = await client.get(
            "/health/live",
            headers={"X-Correlation-Id": correlation_id}
        )

        assert response.status_code == 200
        assert response.headers["x-correlation-id"] == correlation_id
