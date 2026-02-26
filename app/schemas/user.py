from datetime import datetime
from pydantic import BaseModel

from app.schemas.common import PageResponse


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Convenience alias for list endpoints
UserListResponse = PageResponse[UserResponse]
