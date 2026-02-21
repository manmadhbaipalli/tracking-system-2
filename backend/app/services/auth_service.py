"""
Claims Service Platform - Authentication Service

Handles user login, token management, role validation, and session management.
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.services.audit_service import audit_service


class AuthService:
    """Service for handling authentication and authorization"""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str, ip_address: str = None) -> Optional[User]:
        """Authenticate user with username and password"""
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return None

        # Check if account is locked
        if user.is_account_locked:
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            user.increment_failed_login()
            db.commit()

            # Log failed login attempt
            audit_service.log_action(
                db=db,
                user_id=user.id,
                action="login_failed",
                table_name="users",
                record_id=str(user.id),
                description="Failed login attempt",
                ip_address=ip_address,
                success="failure"
            )

            return None

        # Update successful login
        user.update_last_login()
        db.commit()

        # Log successful login
        audit_service.log_action(
            db=db,
            user_id=user.id,
            action="login",
            table_name="users",
            record_id=str(user.id),
            description="Successful login",
            ip_address=ip_address
        )

        return user

    @staticmethod
    def create_tokens(user: User) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value if user.role else "viewer",
            "email": user.email
        }

        access_token = create_access_token(token_data, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_info": user.to_dict()
        }

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "viewer",
        created_by: Optional[int] = None
    ) -> User:
        """Create new user"""
        hashed_password = get_password_hash(password)

        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            created_by=created_by
        )

        user.generate_full_name()

        db.add(user)
        db.commit()
        db.refresh(user)

        # Log user creation
        audit_service.log_action(
            db=db,
            user_id=created_by,
            action="create",
            table_name="users",
            record_id=str(user.id),
            new_values=user.to_dict(),
            description=f"Created user {username}"
        )

        return user

# Global auth service instance
auth_service = AuthService()