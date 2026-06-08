from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictions import Prediction, SpecialPrediction


class PredictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_prediction(self, prediction: Prediction) -> Prediction:
        self.session.add(prediction)
        await self.session.commit()
        await self.session.refresh(prediction)
        return prediction

    async def update_prediction(self, prediction: Prediction) -> Prediction:
        await self.session.commit()
        await self.session.refresh(prediction)
        return prediction

    async def get_prediction(
        self,
        user_id: UUID,
        league_id: UUID,
        match_id: UUID,
    ) -> Prediction | None:
        result = await self.session.execute(
            select(Prediction).where(
                Prediction.user_id == user_id,
                Prediction.league_id == league_id,
                Prediction.match_id == match_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_prediction_by_id(self, prediction_id: UUID) -> Prediction | None:
        result = await self.session.execute(select(Prediction).where(Prediction.id == prediction_id))
        return result.scalar_one_or_none()

    async def list_user_predictions(
        self,
        user_id: UUID,
        league_id: UUID | None = None,
    ) -> list[Prediction]:
        query = select(Prediction).where(Prediction.user_id == user_id)

        if league_id is not None:
            query = query.where(Prediction.league_id == league_id)

        query = query.order_by(Prediction.submitted_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_match_predictions(
        self,
        match_id: UUID,
        league_id: UUID | None = None,
    ) -> list[Prediction]:
        query = select(Prediction).where(Prediction.match_id == match_id)

        if league_id is not None:
            query = query.where(Prediction.league_id == league_id)

        query = query.order_by(Prediction.submitted_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_special_prediction(
        self,
        special_prediction: SpecialPrediction,
    ) -> SpecialPrediction:
        self.session.add(special_prediction)
        await self.session.commit()
        await self.session.refresh(special_prediction)
        return special_prediction

    async def get_special_prediction(
        self,
        user_id: UUID,
        league_id: UUID,
        category: str,
    ) -> SpecialPrediction | None:
        result = await self.session.execute(
            select(SpecialPrediction).where(
                SpecialPrediction.user_id == user_id,
                SpecialPrediction.league_id == league_id,
                SpecialPrediction.category == category,
            )
        )
        return result.scalar_one_or_none()

    async def list_user_special_predictions(
        self,
        user_id: UUID,
        league_id: UUID | None = None,
    ) -> list[SpecialPrediction]:
        query = select(SpecialPrediction).where(SpecialPrediction.user_id == user_id)

        if league_id is not None:
            query = query.where(SpecialPrediction.league_id == league_id)

        query = query.order_by(SpecialPrediction.submitted_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())
