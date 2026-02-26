# Project: simple-python-app

## Overview
A simple Python FastAPI application with user management, JWT authentication, and health checks.

## Package Structure
```
app/
  config.py         # Pydantic Settings
  database.py       # SQLAlchemy async session
  exceptions.py     # Custom exceptions
  security.py       # JWT + password hashing
  middleware.py     # Correlation ID + request logging
  main.py           # FastAPI entry point
  models/           # SQLAlchemy models
  schemas/          # Pydantic schemas (DTOs)
  routers/          # FastAPI routers
  services/         # Business logic
```

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --reload

# Verify imports
python -c "from app.main import app; print('OK')"
```

## Conventions
- Async SQLAlchemy with aiosqlite
- Pydantic v2 schemas
- JWT via python-jose
- Passwords hashed with passlib/bcrypt
- Always use `datetime.now(timezone.utc)` (not `datetime.utcnow()`)
