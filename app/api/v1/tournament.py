from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.scoring import get_scoring_service
from app.core.dependencies import get_current_user
from app.db.connection import get_db_session
from app.models.enums import MatchStage, MatchStatus
from app.models.users import User
from app.repositories.tournament import TournamentRepository
from app.schemas.tournament import (
    MatchCreate,
    MatchResponse,
    MatchResultUpdate,
    PlayerCreate,
    PlayerResponse,
    TeamCreate,
    TeamResponse,
)
from app.services.scoring import ScoringService
from app.services.tournament import TournamentService

router = APIRouter(tags=["Tournament"])


def get_tournament_service(
    session: AsyncSession = Depends(get_db_session),
) -> TournamentService:
    repository = TournamentRepository(session)
    return TournamentService(repository)


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.create_team(data, current_user)


@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(
    group_letter: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.list_teams(group_letter)


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.get_team(team_id)


@router.post("/players", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    data: PlayerCreate,
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.create_player(data, current_user)


@router.get("/players", response_model=list[PlayerResponse])
async def list_players(
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.list_players()


@router.get("/teams/{team_id}/players", response_model=list[PlayerResponse])
async def list_players_by_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.list_players_by_team(team_id)


@router.post("/matches", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    data: MatchCreate,
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.create_match(data, current_user)


@router.get("/matches", response_model=list[MatchResponse])
async def list_matches(
    stage: MatchStage | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.list_matches(stage)


@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TournamentService = Depends(get_tournament_service),
):
    return await service.get_match(match_id)


@router.patch("/matches/{match_id}/result", response_model=MatchResponse)
async def update_match_result(
    match_id: UUID,
    data: MatchResultUpdate,
    current_user: User = Depends(get_current_user),
    tournament_service: TournamentService = Depends(get_tournament_service),
    scoring_service: ScoringService = Depends(get_scoring_service),
):
    match = await tournament_service.update_match_result(match_id, data, current_user)
    if match.status == MatchStatus.FINISHED:
        await scoring_service.recalculate_match_scores(match_id, current_user)
    return match
