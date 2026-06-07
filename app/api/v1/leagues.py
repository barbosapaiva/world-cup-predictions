from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.connection import get_db_session
from app.models.users import User
from app.repositories.leagues import LeagueRepository
from app.schemas.leagues import AddMemberRequest, LeagueCreate, LeagueMemberResponse, LeagueResponse
from app.services.leagues import LeagueService

router = APIRouter(prefix="/leagues", tags=["Leagues"])


def get_league_service(
    session: AsyncSession = Depends(get_db_session),
) -> LeagueService:
    return LeagueService(LeagueRepository(session))


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    data: LeagueCreate,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    return await service.create_league(data, current_user)


@router.get("", response_model=list[LeagueResponse])
async def list_my_leagues(
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    return await service.list_user_leagues(current_user.id)


@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    return await service.get_league(league_id)


@router.post(
    "/{league_id}/members",
    response_model=LeagueMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    league_id: UUID,
    data: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    return await service.add_member(league_id, data, current_user)


@router.get("/{league_id}/members", response_model=list[LeagueMemberResponse])
async def list_members(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    return await service.list_members(league_id, current_user)
