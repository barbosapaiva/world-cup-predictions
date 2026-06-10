from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    invite_code: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    is_superadmin: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
