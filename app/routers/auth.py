from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services import auth_service
from app.security import get_current_user_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **name**: User's full name
    """
    return await auth_service.register_user(session, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    """
    Authenticate user and get access token.

    - **email**: User's email address
    - **password**: User's password

    Returns JWT access token for authenticated requests.
    """
    return await auth_service.login_user(session, data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    """
    Get current authenticated user profile.

    Requires valid JWT token in Authorization header:
    `Authorization: Bearer <token>`
    """
    return await auth_service.get_current_user(session, user_id)
