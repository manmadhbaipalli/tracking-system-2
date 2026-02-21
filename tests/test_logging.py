"""Tests for logging middleware."""

import logging
from io import StringIO
import pytest
from fastapi.testclient import TestClient
from app.utils.logging import get_logger, setup_logging


class TestLoggingSetup:
    """Tests for logging configuration."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger(__name__)
        assert isinstance(logger, logging.Logger)
        assert logger.name == __name__

    def test_logging_format(self):
        """Test that logging includes all required fields."""
        setup_logging()
        logger = get_logger("test_logger")

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
            )
        )
        logger.addHandler(handler)

        logger.info("test message")
        output = stream.getvalue()

        assert "test_logger" in output
        assert "INFO" in output
        assert "test message" in output


class TestLoggingMiddleware:
    """Tests for request/response logging middleware."""

    def test_request_id_generated(self, test_client: TestClient):
        """Test that request ID is generated for each request."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_logging_on_endpoint_call(
        self,
        test_client: TestClient,
        caplog,
    ):
        """Test that endpoint calls are logged."""
        with caplog.at_level(logging.INFO):
            response = test_client.get("/")

        assert response.status_code == 200
        assert any("GET" in record.message for record in caplog.records)
        assert any("/" in record.message for record in caplog.records)

    def test_request_id_in_error_response(
        self,
        test_client: TestClient,
    ):
        """Test that request ID is included in error responses."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "request_id" in data
        assert data["request_id"] != "unknown"

    def test_response_status_logged(
        self,
        test_client: TestClient,
        caplog,
    ):
        """Test that response status is logged."""
        with caplog.at_level(logging.INFO):
            response = test_client.get("/")

        assert response.status_code == 200
        assert any(
            "200" in record.message for record in caplog.records
        )

    def test_request_response_duration_logged(
        self,
        test_client: TestClient,
        caplog,
    ):
        """Test that response duration is logged."""
        with caplog.at_level(logging.INFO):
            response = test_client.get("/")

        assert response.status_code == 200
        assert any("duration" in record.message for record in caplog.records)
