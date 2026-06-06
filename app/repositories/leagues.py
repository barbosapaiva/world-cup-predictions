from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leagues import League, LeagueMember


class LeagueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_with_admin_member(
        self,
        league: League,
        member: LeagueMember,
    ) -> League:
        self.session.add(league)
        await self.session.flush()

        member.league_id = league.id
        self.session.add(member)

        await self.session.commit()
        await self.session.refresh(league)

        return league

    async def get_by_id(self, league_id: UUID) -> League | None:
        result = await self.session.execute(select(League).where(League.id == league_id))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[League]:
        result = await self.session.execute(
            select(League)
            .join(LeagueMember, LeagueMember.league_id == League.id)
            .where(
                LeagueMember.user_id == user_id,
                LeagueMember.is_active.is_(True),
            )
            .order_by(League.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_member(self, member: LeagueMember) -> LeagueMember:
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_member(
        self,
        user_id: UUID,
        league_id: UUID,
    ) -> LeagueMember | None:
        result = await self.session.execute(
            select(LeagueMember).where(
                LeagueMember.user_id == user_id,
                LeagueMember.league_id == league_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_members(self, league_id: UUID) -> list[LeagueMember]:
        result = await self.session.execute(
            select(LeagueMember).where(LeagueMember.league_id == league_id).order_by(LeagueMember.joined_at.asc())
        )
        return list(result.scalars().all())

    async def update(self, league: League) -> League:
        await self.session.commit()
        await self.session.refresh(league)
        return league
