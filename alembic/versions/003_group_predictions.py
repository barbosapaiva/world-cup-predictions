"""add group_predictions table

Revision ID: 003_group_predictions
Revises: 002_invite_code
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003_group_predictions"
down_revision: Union[str, None] = "002_invite_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_predictions",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("league_id", UUID(), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("group_letter", sa.CHAR(1), nullable=False),
        sa.Column("first_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("second_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("third_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("fourth_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("points_awarded", sa.Integer(), nullable=True),
        sa.UniqueConstraint("user_id", "league_id", "group_letter", name="uq_group_pred_user_league_group"),
        sa.CheckConstraint("points_awarded IS NULL OR (points_awarded >= 0 AND points_awarded <= 4)", name="chk_group_pred_points"),
        sa.CheckConstraint(
            "first_team_id != second_team_id AND first_team_id != third_team_id AND first_team_id != fourth_team_id "
            "AND second_team_id != third_team_id AND second_team_id != fourth_team_id "
            "AND third_team_id != fourth_team_id",
            name="chk_group_pred_distinct_teams",
        ),
    )
    op.create_index("idx_group_pred_user_league", "group_predictions", ["user_id", "league_id"])
    op.create_index("idx_group_pred_group", "group_predictions", ["group_letter"])


def downgrade() -> None:
    op.drop_index("idx_group_pred_group", table_name="group_predictions")
    op.drop_index("idx_group_pred_user_league", table_name="group_predictions")
    op.drop_table("group_predictions")
