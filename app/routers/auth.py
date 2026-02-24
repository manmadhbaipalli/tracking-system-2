from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, RegisterResponse, TokenResponse
from app.services.auth_service import register_user, login_user
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account and return an access token.",
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, token = await register_user(db, request.email, request.password, request.full_name)
    return RegisterResponse(
        user=user,
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Authenticate with email and password, returns a JWT access token.",
)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, token = await login_user(db, request.email, request.password)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60,
    )
