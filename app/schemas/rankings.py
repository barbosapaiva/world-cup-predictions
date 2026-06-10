from uuid import UUID

from pydantic import BaseModel


class RankingEntryResponse(BaseModel):
    position: int
    user_id: UUID
    name: str
    total_points: int
    match_points: int
    special_prediction_points: int
    exact_scores: int
    outcome_hits: int
    group_position_points: int
    group_prediction_points: int

    model_config = {"from_attributes": True}
