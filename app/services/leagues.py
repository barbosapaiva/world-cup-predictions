import secrets
import string
from uuid import UUID

from fastapi import HTTPException, status

from app.models.enums import UserRole
from app.models.leagues import League, LeagueMember
from app.models.users import User
from app.repositories.leagues import LeagueRepository
from app.schemas.leagues import AddMemberRequest, LeagueCreate


class LeagueService:
    def __init__(self, repository: LeagueRepository):
        self.repository = repository

    @staticmethod
    def _generate_invite_code(length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_league(self, data: LeagueCreate, current_user: User) -> League:
        league = League(
            name=data.name,
            rules=data.rules,
            season=data.season,
            invite_code=self._generate_invite_code(),
            created_by=current_user.id,
        )

        member = LeagueMember(
            user_id=current_user.id,
            role=UserRole.ADMIN,
        )

        return await self.repository.create_with_admin_member(league, member)

    async def get_league(self, league_id: UUID) -> League:
        league = await self.repository.get_by_id(league_id)

        if league is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found",
            )

        return league

    async def list_user_leagues(self, user_id: UUID) -> list[League]:
        return await self.repository.list_by_user(user_id)

    async def add_member(
        self,
        league_id: UUID,
        data: AddMemberRequest,
        current_user: User,
    ) -> LeagueMember:
        league = await self.get_league(league_id)

        current_member = await self.repository.get_member(
            user_id=current_user.id,
            league_id=league.id,
        )

        if current_member is None or current_member.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only league admins can add members",
            )

        existing_member = await self.repository.get_member(
            user_id=data.user_id,
            league_id=league.id,
        )

        if existing_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this league",
            )

        member = LeagueMember(
            user_id=data.user_id,
            league_id=league.id,
            role=data.role,
        )

        return await self.repository.add_member(member)

    async def join_by_invite_code(self, invite_code: str, current_user: User) -> LeagueMember:
        league = await self.repository.get_by_invite_code(invite_code)

        if league is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invite code",
            )

        existing_member = await self.repository.get_member(
            user_id=current_user.id,
            league_id=league.id,
        )

        if existing_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already a member of this league",
            )

        member = LeagueMember(
            user_id=current_user.id,
            league_id=league.id,
            role=UserRole.PARTICIPANT,
        )

        return await self.repository.add_member(member)

    async def list_members(
        self,
        league_id: UUID,
        current_user: User,
    ) -> list[LeagueMember]:
        league = await self.get_league(league_id)

        current_member = await self.repository.get_member(
            user_id=current_user.id,
            league_id=league.id,
        )

        if current_member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only league members can view members",
            )

        return await self.repository.list_members(league.id)
