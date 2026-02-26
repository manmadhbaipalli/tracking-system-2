from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse
from app.exceptions import ConflictException, AuthException, ForbiddenException
from app.config import settings


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = UserRepository(db)

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        existing = await self._repo.get_by_email(request.email)
        if existing is not None:
            raise ConflictException("Email address is already registered", "EMAIL_CONFLICT")

        password_hash = hash_password(request.password)
        user = await self._repo.create(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
        )

        token = create_access_token(subject=str(user.id))
        expires_in = settings.access_token_expire_minutes * 60

        return RegisterResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse.model_validate(user),
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthException("Invalid email or password", "INVALID_CREDENTIALS")

        if not user.active:
            raise ForbiddenException("Account is deactivated", "ACCOUNT_DEACTIVATED")

        token = create_access_token(subject=str(user.id))
        expires_in = settings.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
        )
