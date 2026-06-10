"""add invite_code to leagues

Revision ID: 002_invite_code
Revises: 001_baseline
Create Date: 2026-06-10

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_invite_code"
down_revision: str | None = "001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leagues", sa.Column("invite_code", sa.String(20), nullable=True))

    # Backfill existing rows with random 8-char codes
    op.execute(
        "UPDATE leagues SET invite_code = UPPER(SUBSTRING(REPLACE(gen_random_uuid()::text, '-', '') FROM 1 FOR 8)) "
        "WHERE invite_code IS NULL"
    )

    op.alter_column("leagues", "invite_code", nullable=False)
    op.create_unique_constraint("uq_leagues_invite_code", "leagues", ["invite_code"])
    op.create_index("ix_leagues_invite_code", "leagues", ["invite_code"])


def downgrade() -> None:
    op.drop_index("ix_leagues_invite_code", table_name="leagues")
    op.drop_constraint("uq_leagues_invite_code", "leagues", type_="unique")
    op.drop_column("leagues", "invite_code")
