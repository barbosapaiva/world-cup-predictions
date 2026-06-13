from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.connection import get_db_session
from app.models.users import User
from app.repositories.group_predictions import GroupPredictionRepository
from app.repositories.leagues import LeagueRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.group_predictions import (
    GroupPredictionCreate,
    GroupPredictionResponse,
    GroupStandingEntry,
)
from app.services.group_predictions import GroupPredictionService

router = APIRouter(prefix="/leagues/{league_id}/group-predictions", tags=["Group Predictions"])


def get_service(session: AsyncSession = Depends(get_db_session)) -> GroupPredictionService:
    return GroupPredictionService(
        GroupPredictionRepository(session),
        LeagueRepository(session),
        TournamentRepository(session),
    )


@router.post("", response_model=GroupPredictionResponse, status_code=status.HTTP_201_CREATED)
async def submit_group_prediction(
    league_id: UUID,
    data: GroupPredictionCreate,
    current_user: User = Depends(get_current_user),
    service: GroupPredictionService = Depends(get_service),
):
    return await service.submit_prediction(league_id, data, current_user)


@router.get("", response_model=list[GroupPredictionResponse])
async def list_my_group_predictions(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: GroupPredictionService = Depends(get_service),
):
    return await service.list_my_predictions(league_id, current_user)


@router.get("/all", response_model=list[GroupPredictionResponse])
async def list_all_group_predictions(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: GroupPredictionService = Depends(get_service),
):
    return await service.list_all_league_predictions(league_id, current_user)


@router.get("/standings/{group_letter}", response_model=list[GroupStandingEntry])
async def get_group_standings(
    league_id: UUID,
    group_letter: str,
    current_user: User = Depends(get_current_user),
    service: GroupPredictionService = Depends(get_service),
):
    return await service.get_group_standings(group_letter.upper())
