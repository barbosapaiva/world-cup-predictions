from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.connection import get_db_session
from app.models.users import User
from app.repositories.leagues import LeagueRepository
from app.repositories.rankings import RankingRepository
from app.schemas.rankings import RankingEntryResponse
from app.services.rankings import RankingService

router = APIRouter(tags=["Rankings"])


def get_ranking_service(
    session: AsyncSession = Depends(get_db_session),
) -> RankingService:
    ranking_repository = RankingRepository(session)
    league_repository = LeagueRepository(session)

    return RankingService(
        ranking_repository=ranking_repository,
        league_repository=league_repository,
    )


@router.get(
    "/leagues/{league_id}/ranking",
    response_model=list[RankingEntryResponse],
)
async def get_league_ranking(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: RankingService = Depends(get_ranking_service),
):
    return await service.get_league_ranking(
        league_id=league_id,
        current_user=current_user,
    )
