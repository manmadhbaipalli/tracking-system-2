from pydantic import BaseModel
from app.models.user import UserRole


class RoleUpdateRequest(BaseModel):
    role: UserRole


class StatusUpdateRequest(BaseModel):
    active: bool