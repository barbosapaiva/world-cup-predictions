from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import SpecialCategory


class PredictionCreate(BaseModel):
    league_id: UUID
    match_id: UUID
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    advancing_team_id: UUID | None = None


class PredictionUpdate(BaseModel):
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    advancing_team_id: UUID | None = None


class PredictionResponse(BaseModel):
    id: UUID
    user_id: UUID
    league_id: UUID
    match_id: UUID
    home_score: int
    away_score: int
    advancing_team_id: UUID | None
    submitted_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SpecialPredictionCreate(BaseModel):
    league_id: UUID
    category: SpecialCategory
    team_id: UUID | None = None
    player_id: UUID | None = None


class SpecialPredictionResponse(BaseModel):
    id: UUID
    user_id: UUID
    league_id: UUID
    category: SpecialCategory
    team_id: UUID | None
    player_id: UUID | None
    submitted_at: datetime

    model_config = {"from_attributes": True}
