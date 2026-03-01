from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services import auth_service
from app.security import get_current_user_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    """Register a new user"""
    user = await auth_service.register_user(session, data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """Login and get JWT token"""
    user, token = await auth_service.login_user(session, data)
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get current authenticated user"""
    user = await auth_service.get_user_by_id(session, user_id)
    return UserResponse.model_validate(user)
