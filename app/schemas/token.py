"""Pydantic schemas for JWT token responses."""
from pydantic import BaseModel


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data schema."""

    username: str | None = None