from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


def utc_now():
    """Helper to get current UTC time"""
    return datetime.now(timezone.utc)
