from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status

from app.models.enums import MatchStage, MatchStatus
from app.models.tournament import Match, Player, Team
from app.models.users import User
from app.repositories.tournament import TournamentRepository
from app.schemas.tournament import MatchCreate, MatchResultUpdate, PlayerCreate, TeamCreate


class TournamentService:
    def __init__(self, repository: TournamentRepository):
        self.repository = repository

    def _require_superadmin(self, current_user: User) -> None:
        if not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmins can perform this action",
            )

    async def create_team(self, data: TeamCreate, current_user: User) -> Team:
        self._require_superadmin(current_user)

        code = data.code.upper()
        existing_team = await self.repository.get_team_by_code(code)

        if existing_team is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Team code already exists",
            )

        team = Team(
            name=data.name,
            code=code,
            flag_url=data.flag_url,
            group_letter=data.group_letter.upper() if data.group_letter else None,
            confederation=data.confederation,
        )

        return await self.repository.create_team(team)

    async def get_team(self, team_id: UUID) -> Team:
        team = await self.repository.get_team_by_id(team_id)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        return team

    async def list_teams(self, group_letter: str | None = None) -> list[Team]:
        if group_letter:
            return await self.repository.list_teams_by_group(group_letter.upper())

        return await self.repository.list_teams()

    async def create_player(self, data: PlayerCreate, current_user: User) -> Player:
        self._require_superadmin(current_user)

        team = await self.repository.get_team_by_id(data.team_id)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        player = Player(
            team_id=data.team_id,
            name=data.name,
            position=data.position,
            birth_date=data.birth_date,
        )

        return await self.repository.create_player(player)

    async def list_players_by_team(self, team_id: UUID) -> list[Player]:
        team = await self.repository.get_team_by_id(team_id)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        return await self.repository.list_players_by_team(team_id)

    async def create_match(self, data: MatchCreate, current_user: User) -> Match:
        self._require_superadmin(current_user)

        existing_match = await self.repository.get_match_by_number(data.match_number)

        if existing_match is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Match number already exists",
            )

        if data.home_team_id is None and data.home_placeholder is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Home team or home placeholder is required",
            )

        if data.away_team_id is None and data.away_placeholder is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Away team or away placeholder is required",
            )

        match = Match(
            home_team_id=data.home_team_id,
            away_team_id=data.away_team_id,
            home_placeholder=data.home_placeholder,
            away_placeholder=data.away_placeholder,
            stage=data.stage,
            group_letter=data.group_letter.upper() if data.group_letter else None,
            match_number=data.match_number,
            match_date=data.match_date,
            venue=data.venue,
            status=MatchStatus.SCHEDULED,
            submission_deadline=data.match_date - timedelta(hours=1),
        )

        return await self.repository.create_match(match)

    async def get_match(self, match_id: UUID) -> Match:
        match = await self.repository.get_match_by_id(match_id)

        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found",
            )

        return match

    async def list_matches(self, stage: MatchStage | None = None) -> list[Match]:
        return await self.repository.list_matches(stage)

    async def update_match_result(
        self,
        match_id: UUID,
        data: MatchResultUpdate,
        current_user: User,
    ) -> Match:
        self._require_superadmin(current_user)

        match = await self.get_match(match_id)

        if match.stage != MatchStage.GROUP:
            if data.home_score == data.away_score and data.advancing_team_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Advancing team is required for knockout draws",
                )

            if data.home_score != data.away_score and data.advancing_team_id is None:
                data.advancing_team_id = match.home_team_id if data.home_score > data.away_score else match.away_team_id

        match.home_score = data.home_score
        match.away_score = data.away_score
        match.advancing_team_id = data.advancing_team_id
        match.status = MatchStatus.FINISHED

        updated_match = await self.repository.update_match(match)

        await self._resolve_bracket_placeholders(updated_match)

        return updated_match

    async def _resolve_bracket_placeholders(self, match: Match) -> None:
        if match.advancing_team_id is None:
            return

        placeholder = f"W{match.match_number}"
        affected_matches = await self.repository.list_matches_by_placeholder(placeholder)

        for affected_match in affected_matches:
            if affected_match.home_placeholder == placeholder:
                affected_match.home_team_id = match.advancing_team_id

            if affected_match.away_placeholder == placeholder:
                affected_match.away_team_id = match.advancing_team_id

            if affected_match.home_team_id and affected_match.away_team_id:
                affected_match.status = MatchStatus.SCHEDULED

            await self.repository.update_match(affected_match)
