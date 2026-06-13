from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.connection import get_db_session
from app.models.users import User
from app.repositories.leagues import LeagueRepository
from app.repositories.predictions import PredictionRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.predictions import (
    PredictionCreate,
    PredictionResponse,
    PredictionUpdate,
    SpecialPredictionCreate,
    SpecialPredictionResponse,
)
from app.services.predictions import PredictionService

router = APIRouter(tags=["Predictions"])


def get_prediction_service(
    session: AsyncSession = Depends(get_db_session),
) -> PredictionService:
    prediction_repository = PredictionRepository(session)
    league_repository = LeagueRepository(session)
    tournament_repository = TournamentRepository(session)

    return PredictionService(
        prediction_repository=prediction_repository,
        league_repository=league_repository,
        tournament_repository=tournament_repository,
    )


@router.post(
    "/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prediction(
    data: PredictionCreate,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    return await service.create_prediction(data, current_user)


@router.patch(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse,
)
async def update_prediction(
    prediction_id: UUID,
    data: PredictionUpdate,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    return await service.update_prediction(prediction_id, data, current_user)


@router.get("/predictions/me", response_model=list[PredictionResponse])
async def list_my_predictions(
    league_id: UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    return await service.list_my_predictions(current_user, league_id)


@router.get(
    "/predictions/matches/{match_id}",
    response_model=list[PredictionResponse],
)
async def list_match_predictions(
    match_id: UUID,
    league_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):

    return await service.list_match_predictions(
        match_id=match_id,
        current_user=current_user,
        league_id=league_id,
    )


@router.post(
    "/special-predictions",
    response_model=SpecialPredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_special_prediction(
    data: SpecialPredictionCreate,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    return await service.create_special_prediction(data, current_user)


@router.get(
    "/special-predictions/me",
    response_model=list[SpecialPredictionResponse],
)
async def list_my_special_predictions(
    league_id: UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    return await service.list_my_special_predictions(current_user, league_id)


@router.get(
    "/special-predictions/league/{league_id}",
    response_model=list[SpecialPredictionResponse],
)
async def list_league_special_predictions(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    return await service.list_league_special_predictions(league_id, current_user)
