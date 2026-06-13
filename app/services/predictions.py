from datetime import UTC, date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.models.enums import MatchStage, MatchStatus, PlayerPosition, SpecialCategory
from app.models.predictions import Prediction, SpecialPrediction
from app.models.tournament import Match
from app.models.users import User
from app.repositories.leagues import LeagueRepository
from app.repositories.predictions import PredictionRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.predictions import (
    PredictionCreate,
    PredictionUpdate,
    SpecialPredictionCreate,
)

# Special predictions deadline: first game second hand matchday end (18 June 2026, 17:00 UTC)
SPECIAL_PREDICTIONS_DEADLINE = datetime(2026, 6, 18, 17, 0, 0, tzinfo=timezone.utc)

# Young player cutoff: born on or after 1 Jan 2005 (max 21 years old)
YOUNG_PLAYER_CUTOFF = date(2005, 1, 1)


class PredictionService:
    def __init__(
        self,
        prediction_repository: PredictionRepository,
        league_repository: LeagueRepository,
        tournament_repository: TournamentRepository,
    ):
        self.prediction_repository = prediction_repository
        self.league_repository = league_repository
        self.tournament_repository = tournament_repository

    async def create_prediction(
        self,
        data: PredictionCreate,
        current_user: User,
    ) -> Prediction:
        await self._validate_league_membership(data.league_id, current_user.id)

        match = await self.tournament_repository.get_match_by_id(data.match_id)

        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found",
            )

        self._validate_match_teams_are_defined(match)
        self._validate_match_is_predictable(match)
        self._validate_knockout_prediction(data, match)

        existing_prediction = await self.prediction_repository.get_prediction(
            user_id=current_user.id,
            league_id=data.league_id,
            match_id=data.match_id,
        )

        if existing_prediction is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Prediction already exists for this match and league",
            )

        prediction = Prediction(
            user_id=current_user.id,
            league_id=data.league_id,
            match_id=data.match_id,
            home_score=data.home_score,
            away_score=data.away_score,
            advancing_team_id=data.advancing_team_id,
        )

        return await self.prediction_repository.create_prediction(prediction)

    async def update_prediction(
        self,
        prediction_id: UUID,
        data: PredictionUpdate,
        current_user: User,
    ) -> Prediction:
        prediction = await self.prediction_repository.get_prediction_by_id(prediction_id)

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found",
            )

        if prediction.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own predictions",
            )

        match = await self.tournament_repository.get_match_by_id(prediction.match_id)

        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found",
            )

        self._validate_match_is_predictable(match)

        update_data = data.model_dump(exclude_unset=True)

        home_score = update_data.get("home_score", prediction.home_score)
        away_score = update_data.get("away_score", prediction.away_score)

        prediction.home_score = home_score
        prediction.away_score = away_score

        if "advancing_team_id" in update_data:
            prediction.advancing_team_id = update_data["advancing_team_id"]

        self._validate_knockout_prediction(
            PredictionCreate(
                league_id=prediction.league_id,
                match_id=prediction.match_id,
                home_score=prediction.home_score,
                away_score=prediction.away_score,
                advancing_team_id=prediction.advancing_team_id,
            ),
            match,
        )

        prediction.updated_at = datetime.now(UTC)

        return await self.prediction_repository.update_prediction(prediction)

    async def list_my_predictions(
        self,
        current_user: User,
        league_id: UUID | None = None,
    ) -> list[Prediction]:
        return await self.prediction_repository.list_user_predictions(
            user_id=current_user.id,
            league_id=league_id,
        )

    async def list_match_predictions(
        self,
        match_id: UUID,
        current_user: User,
        league_id: UUID,
    ) -> list[Prediction]:

        match = await self.tournament_repository.get_match_by_id(match_id)

        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found",
            )

        await self._validate_league_membership(
            league_id=league_id,
            user_id=current_user.id,
        )

        return await self.prediction_repository.list_match_predictions(
            match_id=match_id,
            league_id=league_id,
        )

    async def create_special_prediction(
        self,
        data: SpecialPredictionCreate,
        current_user: User,
    ) -> SpecialPrediction:
        await self._validate_league_membership(data.league_id, current_user.id)
        self._validate_special_prediction_target(data)

        # Deadline: 18 June 2026, 17:00 UTC (end of first matchday)
        if datetime.now(UTC) >= SPECIAL_PREDICTIONS_DEADLINE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Special predictions deadline has passed (18 Jun 17:00)",
            )

        # Validate player constraints for specific categories
        if data.player_id is not None:
            await self._validate_player_for_category(data.player_id, data.category)

        existing_prediction = await self.prediction_repository.get_special_prediction(
            user_id=current_user.id,
            league_id=data.league_id,
            category=data.category,
        )

        if existing_prediction is not None:
            existing_prediction.team_id = data.team_id
            existing_prediction.player_id = data.player_id
            existing_prediction.submitted_at = datetime.now(UTC)
            return await self.prediction_repository.update_special_prediction(existing_prediction)

        special_prediction = SpecialPrediction(
            user_id=current_user.id,
            league_id=data.league_id,
            category=data.category,
            team_id=data.team_id,
            player_id=data.player_id,
        )

        return await self.prediction_repository.create_special_prediction(special_prediction)

    async def _validate_player_for_category(
        self,
        player_id: UUID,
        category: SpecialCategory,
    ) -> None:
        player = await self.tournament_repository.get_player_by_id(player_id)
        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )

        if category == SpecialCategory.BEST_GK:
            if player.position != PlayerPosition.GK:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Best GK prediction requires a goalkeeper",
                )

        if category == SpecialCategory.YOUNG_PLAYER:
            if player.birth_date is None or player.birth_date < YOUNG_PLAYER_CUTOFF:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Young player prediction requires a player under 21",
                )

    async def list_my_special_predictions(
        self,
        current_user: User,
        league_id: UUID | None = None,
    ) -> list[SpecialPrediction]:
        return await self.prediction_repository.list_user_special_predictions(
            user_id=current_user.id,
            league_id=league_id,
        )

    async def list_league_special_predictions(
        self,
        league_id: UUID,
        current_user: User,
    ) -> list[SpecialPrediction]:
        await self._validate_league_membership(league_id, current_user.id)

        now = datetime.now(UTC)
        if now < SPECIAL_PREDICTIONS_DEADLINE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Special predictions are not yet closed",
            )

        return await self.prediction_repository.list_league_special_predictions(league_id)

    async def _validate_league_membership(
        self,
        league_id: UUID,
        user_id: UUID,
    ) -> None:
        league = await self.league_repository.get_by_id(league_id)

        if league is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found",
            )

        member = await self.league_repository.get_member(
            user_id=user_id,
            league_id=league_id,
        )

        if member is None or not member.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not an active member of this league",
            )

    def _validate_match_is_predictable(self, match) -> None:
        now = datetime.now(UTC)

        if match.status == MatchStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot predict a finished match",
            )

        if now >= match.submission_deadline:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Prediction deadline has passed",
            )

    def _validate_knockout_prediction(
        self,
        data: PredictionCreate,
        match,
    ) -> None:

        if match.stage == MatchStage.GROUP:
            return

        is_draw = data.home_score == data.away_score

        if is_draw and data.advancing_team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Advancing team is required for knockout draws",
            )

        self._validate_advancing_team(data.advancing_team_id, match)

    def _validate_special_prediction_target(
        self,
        data: SpecialPredictionCreate,
    ) -> None:
        if data.category == SpecialCategory.CHAMPION:
            if data.team_id is None or data.player_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Champion prediction requires team_id only",
                )
            return

        if data.player_id is None or data.team_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Individual award predictions require player_id only",
            )

    def _validate_advancing_team(
        self,
        advancing_team_id: UUID | None,
        match: Match,
    ) -> None:

        if advancing_team_id is None:
            return

        valid_team_ids = {team_id for team_id in [match.home_team_id, match.away_team_id] if team_id is not None}

        if advancing_team_id not in valid_team_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Advancing team must be one of the match teams",
            )

    def _validate_match_teams_are_defined(self, match) -> None:

        if match.home_team_id is None or match.away_team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot predict a match before both teams are defined",
            )
