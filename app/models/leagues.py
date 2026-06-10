from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole


def generate_invite_code() -> str:
    return uuid4().hex[:8].upper()


class League(TimestampMixin, Base):
    __tablename__ = "leagues"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rules: Mapped[str | None] = mapped_column(Text)
    season: Mapped[str] = mapped_column(String(20), nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, default=generate_invite_code)


class LeagueMember(Base):
    __tablename__ = "league_members"

    __table_args__ = (UniqueConstraint("user_id", "league_id", name="uq_league_members_user_league"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=UserRole.PARTICIPANT,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", lazy="raise")

    @property
    def user_name(self) -> str:
        return self.user.name
