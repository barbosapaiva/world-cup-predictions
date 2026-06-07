from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import MatchStage, MatchStatus, PlayerPosition


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=3, max_length=3)
    flag_url: str | None = None
    group_letter: str | None = Field(default=None, min_length=1, max_length=1)
    confederation: str | None = Field(default=None, max_length=20)


class TeamResponse(BaseModel):
    id: UUID
    name: str
    code: str
    flag_url: str | None
    group_letter: str | None
    confederation: str | None

    model_config = {"from_attributes": True}


class PlayerCreate(BaseModel):
    team_id: UUID
    name: str = Field(min_length=2, max_length=150)
    position: PlayerPosition
    birth_date: date | None = None


class PlayerResponse(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    position: PlayerPosition
    birth_date: date | None

    model_config = {"from_attributes": True}


class MatchCreate(BaseModel):
    home_team_id: UUID | None = None
    away_team_id: UUID | None = None
    home_placeholder: str | None = Field(default=None, max_length=10)
    away_placeholder: str | None = Field(default=None, max_length=10)
    stage: MatchStage
    group_letter: str | None = Field(default=None, min_length=1, max_length=1)
    match_number: int
    match_date: datetime
    venue: str | None = Field(default=None, max_length=200)


class MatchResponse(BaseModel):
    id: UUID
    home_team_id: UUID | None
    away_team_id: UUID | None
    home_placeholder: str | None
    away_placeholder: str | None
    stage: MatchStage
    group_letter: str | None
    match_number: int
    match_date: datetime
    venue: str | None
    status: MatchStatus
    submission_deadline: datetime
    home_score: int | None
    away_score: int | None
    advancing_team_id: UUID | None

    model_config = {"from_attributes": True}


class MatchResultUpdate(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    advancing_team_id: UUID | None = None
