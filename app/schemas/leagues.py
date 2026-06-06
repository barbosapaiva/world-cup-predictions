from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import UserRole


# Leagues
class LeagueCreate(BaseModel):
    name: str
    rules: str | None = None
    season: str


class LeagueResponse(BaseModel):
    id: UUID
    name: str
    rules: str | None
    season: str
    created_by: UUID
    created_at: datetime
    model_config = {"from_attributes": True}


# Members
class AddMemberRequest(BaseModel):
    user_id: UUID
    role: UserRole = UserRole.PARTICIPANT


class LeagueMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    league_id: UUID
    role: UserRole
    joined_at: datetime
    is_active: bool
    model_config = {"from_attributes": True}
