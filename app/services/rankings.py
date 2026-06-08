from uuid import UUID

from fastapi import HTTPException, status

from app.models.users import User
from app.repositories.leagues import LeagueRepository
from app.repositories.rankings import RankingRepository


class RankingService:
    def __init__(
        self,
        ranking_repository: RankingRepository,
        league_repository: LeagueRepository,
    ):
        self.ranking_repository = ranking_repository
        self.league_repository = league_repository

    async def get_league_ranking(
        self,
        league_id: UUID,
        current_user: User,
    ) -> list[dict]:
        league = await self.league_repository.get_by_id(league_id)

        if league is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found",
            )

        member = await self.league_repository.get_member(
            user_id=current_user.id,
            league_id=league_id,
        )

        if member is None or not member.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only league members can view this ranking",
            )

        return await self.ranking_repository.get_league_ranking(league_id)
