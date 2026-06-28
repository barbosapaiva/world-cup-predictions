from uuid import UUID

from fastapi import HTTPException, status

from app.models.enums import MatchStatus, SpecialCategory
from app.models.predictions import Prediction, PredictionScore, SpecialPredictionScore
from app.models.users import User
from app.repositories.scoring import ScoringRepository
from app.repositories.tournament import TournamentRepository


class ScoringService:
    EXACT_SCORE_POINTS = 3
    OUTCOME_POINTS = 1
    ADVANCING_TEAM_POINTS = 1
    SPECIAL_PREDICTION_POINTS = 6
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
                real_advancing_team_id=match.advancing_team_id,
            )
            scores.append(prediction_score)

        return scores

    async def _calculate_and_save_prediction_score(
        self,
        prediction: Prediction,
        real_home_score: int,
        real_away_score: int,
        real_advancing_team_id=None,
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

        advancing_team_points = self._calculate_advancing_team_points(
            prediction=prediction,
            real_home_score=real_home_score,
            real_away_score=real_away_score,
            real_advancing_team_id=real_advancing_team_id,
        )

        total = exact_score_points + outcome_points + advancing_team_points

        existing_score = await self.scoring_repository.get_prediction_score(prediction.id)

        if existing_score is None:
            prediction_score = PredictionScore(
                prediction_id=prediction.id,
                exact_score_points=exact_score_points,
                outcome_points=outcome_points,
                advancing_team_points=advancing_team_points,
                group_position_points=0,
                total_points=total,
            )

            return await self.scoring_repository.save_prediction_score(prediction_score)

        existing_score.exact_score_points = exact_score_points
        existing_score.outcome_points = outcome_points
        existing_score.advancing_team_points = advancing_team_points
        existing_score.total_points = total + existing_score.group_position_points

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

    def _calculate_advancing_team_points(
        self,
        prediction: Prediction,
        real_home_score: int,
        real_away_score: int,
        real_advancing_team_id=None,
    ) -> int:
        """Bonus point for correctly predicting which team advances in a knockout draw."""
        if (
            prediction.advancing_team_id
            and real_advancing_team_id
            and prediction.home_score == prediction.away_score
            and real_home_score == real_away_score
            and prediction.advancing_team_id == real_advancing_team_id
        ):
            return self.ADVANCING_TEAM_POINTS
        return self.NO_POINTS

    def _get_outcome(self, home_score: int, away_score: int) -> str:
        if home_score > away_score:
            return "home_win"

        if home_score < away_score:
            return "away_win"

        return "draw"

    async def score_special_category(
        self,
        category: SpecialCategory,
        current_user: User,
    ) -> list[SpecialPredictionScore]:
        self._require_superadmin(current_user)

        special_result = await self.scoring_repository.get_special_result(category)

        if special_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No result recorded for category '{category.value}'",
            )

        predictions = await self.scoring_repository.list_special_predictions_by_category(category)

        scores: list[SpecialPredictionScore] = []

        for prediction in predictions:
            score = await self._calculate_and_save_special_score(
                prediction=prediction,
                special_result=special_result,
            )
            scores.append(score)

        return scores

    async def _calculate_and_save_special_score(
        self,
        prediction,
        special_result,
    ) -> SpecialPredictionScore:
        points = self._calculate_special_points(prediction, special_result)

        existing = await self.scoring_repository.get_special_prediction_score(prediction.id)

        if existing is None:
            score = SpecialPredictionScore(
                special_prediction_id=prediction.id,
                points_awarded=points,
            )
            return await self.scoring_repository.save_special_prediction_score(score)

        existing.points_awarded = points
        return await self.scoring_repository.update_special_prediction_score(existing)

    def _calculate_special_points(self, prediction, special_result) -> int:
        if prediction.category == SpecialCategory.CHAMPION:
            if prediction.team_id == special_result.team_id:
                return self.SPECIAL_PREDICTION_POINTS
            return self.NO_POINTS

        if prediction.player_id == special_result.player_id:
            return self.SPECIAL_PREDICTION_POINTS
        return self.NO_POINTS

    def _require_superadmin(self, current_user: User) -> None:
        if not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmins can recalculate scores",
            )
