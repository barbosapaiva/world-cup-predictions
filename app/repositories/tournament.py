from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MatchStage
from app.models.tournament import Match, Player, Team


class TournamentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_team(self, team: Team) -> Team:
        self.session.add(team)
        await self.session.commit()
        await self.session.refresh(team)
        return team

    async def get_team_by_id(self, team_id: UUID) -> Team | None:
        result = await self.session.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()

    async def get_team_by_code(self, code: str) -> Team | None:
        result = await self.session.execute(select(Team).where(Team.code == code))
        return result.scalar_one_or_none()

    async def list_teams(self) -> list[Team]:
        result = await self.session.execute(select(Team).order_by(Team.name.asc()))
        return list(result.scalars().all())

    async def list_teams_by_group(self, group_letter: str) -> list[Team]:
        result = await self.session.execute(
            select(Team).where(Team.group_letter == group_letter).order_by(Team.name.asc())
        )
        return list(result.scalars().all())

    async def create_player(self, player: Player) -> Player:
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def list_players_by_team(self, team_id: UUID) -> list[Player]:
        result = await self.session.execute(select(Player).where(Player.team_id == team_id).order_by(Player.name.asc()))
        return list(result.scalars().all())

    async def create_match(self, match: Match) -> Match:
        self.session.add(match)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def get_match_by_id(self, match_id: UUID) -> Match | None:
        result = await self.session.execute(select(Match).where(Match.id == match_id))
        return result.scalar_one_or_none()

    async def get_match_by_number(self, match_number: int) -> Match | None:
        result = await self.session.execute(select(Match).where(Match.match_number == match_number))
        return result.scalar_one_or_none()

    async def list_matches(self, stage: MatchStage | None = None) -> list[Match]:
        query = select(Match).order_by(Match.match_date.asc())

        if stage is not None:
            query = query.where(Match.stage == stage)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_matches_by_placeholder(self, placeholder: str) -> list[Match]:
        result = await self.session.execute(
            select(Match).where((Match.home_placeholder == placeholder) | (Match.away_placeholder == placeholder))
        )
        return list(result.scalars().all())

    async def update_match(self, match: Match) -> Match:
        await self.session.commit()
        await self.session.refresh(match)
        return match
