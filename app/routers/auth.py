from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new user",
             responses={
                 409: {"description": "Email already exists"},
                 400: {"description": "Validation error"}
             })
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account with email and password.

    Returns a JWT access token upon successful registration.
    Email must be unique and password must meet strength requirements.
    """
    # Service layer will be implemented by the dev agent
    from app.services.auth_service import register_user
    return register_user(db, request)


@router.post("/login", response_model=AuthResponse,
             summary="Authenticate user",
             responses={
                 401: {"description": "Invalid credentials"},
                 400: {"description": "Validation error"}
             })
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password.

    Returns a JWT access token upon successful authentication.
    Token expires in 24 hours (configurable).
    """
    # Service layer will be implemented by the dev agent
    from app.services.auth_service import authenticate_user
    return authenticate_user(db, request)