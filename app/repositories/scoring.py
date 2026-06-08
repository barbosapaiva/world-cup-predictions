from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictions import Prediction, PredictionScore


class ScoringRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_predictions_by_match(self, match_id: UUID) -> list[Prediction]:
        result = await self.session.execute(select(Prediction).where(Prediction.match_id == match_id))
        return list(result.scalars().all())

    async def get_prediction_score(
        self,
        prediction_id: UUID,
    ) -> PredictionScore | None:
        result = await self.session.execute(
            select(PredictionScore).where(PredictionScore.prediction_id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def save_prediction_score(
        self,
        prediction_score: PredictionScore,
    ) -> PredictionScore:
        self.session.add(prediction_score)
        await self.session.commit()
        await self.session.refresh(prediction_score)
        return prediction_score

    async def update_prediction_score(
        self,
        prediction_score: PredictionScore,
    ) -> PredictionScore:
        await self.session.commit()
        await self.session.refresh(prediction_score)
        return prediction_score
