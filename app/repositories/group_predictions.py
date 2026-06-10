from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_predictions import GroupPrediction


class GroupPredictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, prediction: GroupPrediction) -> GroupPrediction:
        existing = await self.get_by_user_league_group(
            prediction.user_id,
            prediction.league_id,
            prediction.group_letter,
        )
        if existing:
            existing.first_team_id = prediction.first_team_id
            existing.second_team_id = prediction.second_team_id
            existing.third_team_id = prediction.third_team_id
            existing.fourth_team_id = prediction.fourth_team_id
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        self.session.add(prediction)
        await self.session.commit()
        await self.session.refresh(prediction)
        return prediction

    async def get_by_user_league_group(
        self,
        user_id: UUID,
        league_id: UUID,
        group_letter: str,
    ) -> GroupPrediction | None:
        result = await self.session.execute(
            select(GroupPrediction).where(
                GroupPrediction.user_id == user_id,
                GroupPrediction.league_id == league_id,
                GroupPrediction.group_letter == group_letter,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user_league(
        self,
        user_id: UUID,
        league_id: UUID,
    ) -> list[GroupPrediction]:
        result = await self.session.execute(
            select(GroupPrediction)
            .where(
                GroupPrediction.user_id == user_id,
                GroupPrediction.league_id == league_id,
            )
            .order_by(GroupPrediction.group_letter)
        )
        return list(result.scalars().all())

    async def list_by_league_group(
        self,
        league_id: UUID,
        group_letter: str,
    ) -> list[GroupPrediction]:
        result = await self.session.execute(
            select(GroupPrediction).where(
                GroupPrediction.league_id == league_id,
                GroupPrediction.group_letter == group_letter,
            )
        )
        return list(result.scalars().all())

    async def update_points(
        self,
        prediction_id: UUID,
        points: int,
    ) -> None:
        await self.session.execute(
            update(GroupPrediction).where(GroupPrediction.id == prediction_id).values(points_awarded=points)
        )
        await self.session.commit()
