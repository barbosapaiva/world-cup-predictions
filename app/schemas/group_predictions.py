from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, model_validator


class GroupPredictionCreate(BaseModel):
    group_letter: str
    first_team_id: UUID
    second_team_id: UUID
    third_team_id: UUID
    fourth_team_id: UUID

    @model_validator(mode="after")
    def teams_must_be_distinct(self):
        ids = [self.first_team_id, self.second_team_id, self.third_team_id, self.fourth_team_id]
        if len(set(ids)) != 4:
            raise ValueError("All four teams must be different")
        return self


class TeamSummary(BaseModel):
    id: UUID
    name: str
    code: str
    flag_url: str | None
    model_config = {"from_attributes": True}


class GroupPredictionResponse(BaseModel):
    id: UUID
    user_id: UUID
    league_id: UUID
    group_letter: str
    first_team_id: UUID
    second_team_id: UUID
    third_team_id: UUID
    fourth_team_id: UUID
    first_team: TeamSummary | None = None
    second_team: TeamSummary | None = None
    third_team: TeamSummary | None = None
    fourth_team: TeamSummary | None = None
    submitted_at: datetime
    updated_at: datetime
    points_awarded: int | None
    model_config = {"from_attributes": True}


class GroupStandingEntry(BaseModel):
    team_id: UUID
    team_name: str
    team_code: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    position: int
