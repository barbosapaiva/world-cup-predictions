"""create match_external_links, drop external_match_id from matches

Revision ID: 004_external_links
Revises: 003_group_predictions
Create Date: 2026-06-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_staging_matches"
down_revision: str = "003_group_predictions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "match_external_links",
        sa.Column(
            "match_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("match_id", "provider"),
    )
    op.create_index("idx_mel_provider_external", "match_external_links", ["provider", "external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_mel_provider_external", table_name="match_external_links")
    op.drop_table("match_external_links")
    op.add_column("matches", sa.Column("external_match_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_matches_external_id", "matches", ["external_match_id"])
    op.create_index("idx_matches_external_id", "matches", ["external_match_id"])
