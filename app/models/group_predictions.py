from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CHAR, DateTime, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class GroupPrediction(Base):
    __tablename__ = "group_predictions"

    __table_args__ = (
        UniqueConstraint("user_id", "league_id", "group_letter", name="uq_group_pred_user_league_group"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    group_letter: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    first_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    second_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    third_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    fourth_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), nullable=False,
    )
    points_awarded: Mapped[int | None] = mapped_column(Integer, nullable=True)

    first_team = relationship("Team", foreign_keys=[first_team_id], lazy="joined")
    second_team = relationship("Team", foreign_keys=[second_team_id], lazy="joined")
    third_team = relationship("Team", foreign_keys=[third_team_id], lazy="joined")
    fourth_team = relationship("Team", foreign_keys=[fourth_team_id], lazy="joined")
