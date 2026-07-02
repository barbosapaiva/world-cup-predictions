"""add advancing_team_points to prediction_scores

Revision ID: 005_advancing_team_points
Revises: 004_staging_matches
Create Date: 2026-06-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_advancing_team_points"
down_revision: str = "004_staging_matches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "prediction_scores",
        sa.Column("advancing_team_points", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_constraint("chk_total_points", "prediction_scores", type_="check")
    op.create_check_constraint(
        "chk_total_points",
        "prediction_scores",
        "total_points = exact_score_points + outcome_points + advancing_team_points + group_position_points",
    )


def downgrade() -> None:
    op.drop_constraint("chk_total_points", "prediction_scores", type_="check")
    op.create_check_constraint(
        "chk_total_points",
        "prediction_scores",
        "total_points = exact_score_points + outcome_points + group_position_points",
    )
    op.drop_column("prediction_scores", "advancing_team_points")
