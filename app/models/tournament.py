from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import MatchStage, MatchStatus, PlayerPosition


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    flag_url: Mapped[str | None] = mapped_column(String(500))
    group_letter: Mapped[str | None] = mapped_column(String(1))
    confederation: Mapped[str | None] = mapped_column(String(20))


class Player(Base):
    __tablename__ = "players"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    position: Mapped[PlayerPosition] = mapped_column(
        Enum(PlayerPosition, name="player_position", create_type=False),
        nullable=False,
    )
    birth_date: Mapped[date | None]


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    home_team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))

    home_placeholder: Mapped[str | None] = mapped_column(String(10))
    away_placeholder: Mapped[str | None] = mapped_column(String(10))

    stage: Mapped[MatchStage] = mapped_column(
        Enum(MatchStage, name="match_stage", create_type=False),
        nullable=False,
    )
    group_letter: Mapped[str | None] = mapped_column(String(1))

    match_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    match_date: Mapped[datetime] = mapped_column(nullable=False)
    venue: Mapped[str | None] = mapped_column(String(200))

    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status", create_type=False),
        default=MatchStatus.SCHEDULED,
        nullable=False,
    )

    submission_deadline: Mapped[datetime] = mapped_column(nullable=False)

    home_score: Mapped[int | None]
    away_score: Mapped[int | None]

    advancing_team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))
