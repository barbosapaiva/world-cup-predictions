from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.connection import get_db_session
from app.models.users import User
from app.repositories.scoring import ScoringRepository
from app.repositories.tournament import TournamentRepository
from app.services.scoring import ScoringService

router = APIRouter(prefix="/scoring", tags=["Scoring"])


def get_scoring_service(
    session: AsyncSession = Depends(get_db_session),
) -> ScoringService:
    scoring_repository = ScoringRepository(session)
    tournament_repository = TournamentRepository(session)

    return ScoringService(
        scoring_repository=scoring_repository,
        tournament_repository=tournament_repository,
    )


@router.post("/matches/{match_id}/recalculate")
async def recalculate_match_scores(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ScoringService = Depends(get_scoring_service),
):
    scores = await service.recalculate_match_scores(
        match_id=match_id,
        current_user=current_user,
    )

    return {
        "match_id": match_id,
        "scores_recalculated": len(scores),
    }
