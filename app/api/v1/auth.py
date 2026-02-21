"""Authentication endpoints for registration and login."""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_database_session
from app.core.config import settings
from app.core.exceptions import UserExistsError
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_database_session),
) -> UserResponse:
    """Register a new user."""
    try:
        user = await create_user(db, user_data)
        logger.info(f"New user registered: {user.email}")
        return UserResponse.model_validate(user)
    except UserExistsError as e:
        logger.warning(f"Registration attempt for existing user: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_database_session),
) -> Token:
    """Authenticate user and return JWT token."""
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user: {user.email}")
    return Token(access_token=access_token)