from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leagues import LeagueMember
from app.models.predictions import Prediction, PredictionScore
from app.models.users import User


class RankingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_league_ranking(self, league_id: UUID) -> list[dict]:
        result = await self.session.execute(
            select(
                User.id.label("user_id"),
                User.name.label("name"),
                func.coalesce(func.sum(PredictionScore.total_points), 0).label("total_points"),
                func.coalesce(
                    func.sum(
                        func.case(
                            (PredictionScore.exact_score_points == 3, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("exact_scores"),
                func.coalesce(
                    func.sum(
                        func.case(
                            (PredictionScore.outcome_points == 1, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("outcome_hits"),
                func.coalesce(
                    func.sum(PredictionScore.group_position_points),
                    0,
                ).label("group_position_points"),
            )
            .select_from(LeagueMember)
            .join(User, User.id == LeagueMember.user_id)
            .outerjoin(
                Prediction,
                (Prediction.user_id == LeagueMember.user_id) & (Prediction.league_id == LeagueMember.league_id),
            )
            .outerjoin(
                PredictionScore,
                PredictionScore.prediction_id == Prediction.id,
            )
            .where(
                LeagueMember.league_id == league_id,
                LeagueMember.is_active.is_(True),
            )
            .group_by(User.id, User.name)
            .order_by(
                desc("total_points"),
                desc("exact_scores"),
                desc("outcome_hits"),
                User.name.asc(),
            )
        )

        rows = result.mappings().all()

        ranking = []
        for index, row in enumerate(rows, start=1):
            ranking.append(
                {
                    "position": index,
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "total_points": row["total_points"],
                    "exact_scores": row["exact_scores"],
                    "outcome_hits": row["outcome_hits"],
                    "group_position_points": row["group_position_points"],
                }
            )

        return ranking
