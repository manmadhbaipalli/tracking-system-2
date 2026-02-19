"""Authentication API endpoints for registration, login, and token refresh."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.dependencies import get_db_session
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegister, session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    """
    Register a new user.

    - **email**: User email address
    - **username**: Unique username
    - **password**: Password (min 8 characters)

    Returns access and refresh tokens along with user info
    """
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin, session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    """
    Login user.

    - **email** (optional): User email
    - **username** (optional): User username
    - **password**: User password

    Requires either email or username. Returns tokens and user info.
    """
    auth_service = AuthService(session)
    return await auth_service.login(
        email=credentials.email,
        username=credentials.username,
        password=credentials.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Refresh access token.

    - **refresh_token**: Valid refresh token

    Returns new access token with same refresh token
    """
    auth_service = AuthService(session)
    return await auth_service.refresh_access_token(request.refresh_token)
