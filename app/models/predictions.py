from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import SpecialCategory


class Prediction(Base):
    __tablename__ = "predictions"

    __table_args__ = (UniqueConstraint("user_id", "match_id", "league_id", name="uq_predictions_user_match_league"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    match_id: Mapped[UUID] = mapped_column(ForeignKey("matches.id"), nullable=False)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    advancing_team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )


class PredictionScore(Base):
    __tablename__ = "prediction_scores"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    prediction_id: Mapped[UUID] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    exact_score_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outcome_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    group_position_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )


class SpecialPrediction(Base):
    __tablename__ = "special_predictions"

    __table_args__ = (
        UniqueConstraint("user_id", "league_id", "category", name="uq_special_predictions_user_league_category"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    category: Mapped[SpecialCategory] = mapped_column(
        Enum(
            SpecialCategory,
            name="special_category",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )

    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[UUID | None] = mapped_column(ForeignKey("players.id"))

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )


class SpecialResult(Base):
    __tablename__ = "special_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    category: Mapped[SpecialCategory] = mapped_column(
        Enum(
            SpecialCategory,
            name="special_category",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        unique=True,
        nullable=False,
    )

    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[UUID | None] = mapped_column(ForeignKey("players.id"))

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
