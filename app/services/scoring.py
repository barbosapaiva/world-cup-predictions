from uuid import UUID

from fastapi import HTTPException, status

from app.models.enums import MatchStatus
from app.models.predictions import Prediction, PredictionScore
from app.models.users import User
from app.repositories.scoring import ScoringRepository
from app.repositories.tournament import TournamentRepository


class ScoringService:
    EXACT_SCORE_POINTS = 3
    OUTCOME_POINTS = 1
    NO_POINTS = 0

    def __init__(
        self,
        scoring_repository: ScoringRepository,
        tournament_repository: TournamentRepository,
    ):
        self.scoring_repository = scoring_repository
        self.tournament_repository = tournament_repository

    async def recalculate_match_scores(
        self,
        match_id: UUID,
        current_user: User,
    ) -> list[PredictionScore]:
        self._require_superadmin(current_user)

        match = await self.tournament_repository.get_match_by_id(match_id)

        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found",
            )

        if match.status != MatchStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Match must be finished before scoring",
            )

        if match.home_score is None or match.away_score is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Match result is required before scoring",
            )

        predictions = await self.scoring_repository.list_predictions_by_match(match_id)

        scores: list[PredictionScore] = []

        for prediction in predictions:
            prediction_score = await self._calculate_and_save_prediction_score(
                prediction=prediction,
                real_home_score=match.home_score,
                real_away_score=match.away_score,
            )
            scores.append(prediction_score)

        return scores

    async def _calculate_and_save_prediction_score(
        self,
        prediction: Prediction,
        real_home_score: int,
        real_away_score: int,
    ) -> PredictionScore:
        exact_score_points = self._calculate_exact_score_points(
            prediction_home_score=prediction.home_score,
            prediction_away_score=prediction.away_score,
            real_home_score=real_home_score,
            real_away_score=real_away_score,
        )

        outcome_points = self._calculate_outcome_points(
            prediction_home_score=prediction.home_score,
            prediction_away_score=prediction.away_score,
            real_home_score=real_home_score,
            real_away_score=real_away_score,
            exact_score_points=exact_score_points,
        )

        existing_score = await self.scoring_repository.get_prediction_score(prediction.id)

        if existing_score is None:
            prediction_score = PredictionScore(
                prediction_id=prediction.id,
                exact_score_points=exact_score_points,
                outcome_points=outcome_points,
                group_position_points=0,
                total_points=exact_score_points + outcome_points,
            )

            return await self.scoring_repository.save_prediction_score(prediction_score)

        existing_score.exact_score_points = exact_score_points
        existing_score.outcome_points = outcome_points
        existing_score.total_points = exact_score_points + outcome_points + existing_score.group_position_points

        return await self.scoring_repository.update_prediction_score(existing_score)

    def _calculate_exact_score_points(
        self,
        prediction_home_score: int,
        prediction_away_score: int,
        real_home_score: int,
        real_away_score: int,
    ) -> int:
        if prediction_home_score == real_home_score and prediction_away_score == real_away_score:
            return self.EXACT_SCORE_POINTS

        return self.NO_POINTS

    def _calculate_outcome_points(
        self,
        prediction_home_score: int,
        prediction_away_score: int,
        real_home_score: int,
        real_away_score: int,
        exact_score_points: int,
    ) -> int:
        if exact_score_points == self.EXACT_SCORE_POINTS:
            return self.NO_POINTS

        predicted_outcome = self._get_outcome(
            prediction_home_score,
            prediction_away_score,
        )
        real_outcome = self._get_outcome(
            real_home_score,
            real_away_score,
        )

        if predicted_outcome == real_outcome:
            return self.OUTCOME_POINTS

        return self.NO_POINTS

    def _get_outcome(self, home_score: int, away_score: int) -> str:
        if home_score > away_score:
            return "home_win"

        if home_score < away_score:
            return "away_win"

        return "draw"

    def _require_superadmin(self, current_user: User) -> None:
        if not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmins can recalculate scores",
            )
