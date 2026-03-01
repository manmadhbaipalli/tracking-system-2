# Python FastAPI Authentication App

## Project Standards

### Package Structure
- `app/` - main application package
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas (DTOs)
- `app/routers/` - FastAPI routers (controllers)
- `app/services/` - business logic layer
- `artifacts/python-app-1/` - project documentation and specs

### Code Style
- Use async/await for all database operations
- Type hints on all function signatures
- Snake_case for functions and variables
- PascalCase for classes
- Use Pydantic for validation and settings
- Use SQLAlchemy 2.0+ async style

### Commands
- Create venv: `python -m venv .venv`
- Activate venv (Windows): `.venv/Scripts/activate`
- Activate venv (Unix): `source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run app: `uvicorn app.main:app --reload`
- Run tests: `pytest`
- Access docs: `http://localhost:8000/docs`

### Dependencies
- FastAPI + Uvicorn for web framework
- SQLAlchemy with aiosqlite for database
- Pydantic for validation
- passlib + bcrypt for password hashing
- python-jose for JWT tokens
- pytest for testing
