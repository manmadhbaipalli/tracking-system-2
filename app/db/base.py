"""SQLAlchemy base model imports for migrations."""
from sqlalchemy.ext.declarative import declarative_base

# Import all models here for Alembic autogenerate
from app.models.user import User  # noqa

Base = declarative_base()