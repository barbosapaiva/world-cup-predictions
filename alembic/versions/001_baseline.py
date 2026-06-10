"""baseline — full initial schema

Revision ID: 001_baseline
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, JSONB

revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enums — create_type=False prevents SQLAlchemy from auto-creating them
user_role = ENUM("admin", "participant", name="user_role", create_type=False)
player_position = ENUM("GK", "DF", "MF", "FW", name="player_position", create_type=False)
match_stage = ENUM("group", "R32", "R16", "QF", "SF", "3rd", "F", name="match_stage", create_type=False)
match_status = ENUM("locked", "scheduled", "live", "finished", name="match_status", create_type=False)
special_category = ENUM("champion", "mvp", "golden_boot", "young_player", "best_gk", name="special_category", create_type=False)


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create enum types explicitly (one per execute for asyncpg)
    op.execute("DO $$ BEGIN CREATE TYPE user_role AS ENUM ('admin', 'participant'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE player_position AS ENUM ('GK', 'DF', 'MF', 'FW'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE match_stage AS ENUM ('group', 'R32', 'R16', 'QF', 'SF', '3rd', 'F'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE match_status AS ENUM ('locked', 'scheduled', 'live', 'finished'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE special_category AS ENUM ('champion', 'mvp', 'golden_boot', 'young_player', 'best_gk'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # USERS
    op.create_table(
        "users",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # LEAGUES
    op.create_table(
        "leagues",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("rules", sa.Text(), nullable=True),
        sa.Column("season", sa.String(20), nullable=False),
        sa.Column("created_by", UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_leagues_created_by", "leagues", ["created_by"])

    # LEAGUE MEMBERS
    op.create_table(
        "league_members",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("league_id", UUID(), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default=sa.text("'participant'")),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("user_id", "league_id", name="uq_league_members_user_league"),
    )
    op.create_index("idx_league_members_user", "league_members", ["user_id"])
    op.create_index("idx_league_members_league", "league_members", ["league_id"])

    # TEAMS
    op.create_table(
        "teams",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(3), nullable=False, unique=True),
        sa.Column("flag_url", sa.String(500), nullable=True),
        sa.Column("group_letter", sa.CHAR(1), nullable=True),
        sa.Column("confederation", sa.String(20), nullable=True),
    )
    op.create_index("idx_teams_group", "teams", ["group_letter"])

    # PLAYERS
    op.create_table(
        "players",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("team_id", UUID(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("position", player_position, nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
    )
    op.create_index("idx_players_team", "players", ["team_id"])

    # MATCHES
    op.create_table(
        "matches",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("home_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("away_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("home_placeholder", sa.String(10), nullable=True),
        sa.Column("away_placeholder", sa.String(10), nullable=True),
        sa.Column("stage", match_stage, nullable=False),
        sa.Column("group_letter", sa.CHAR(1), nullable=True),
        sa.Column("match_number", sa.Integer(), nullable=False, unique=True),
        sa.Column("match_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("status", match_status, nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column("submission_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("advancing_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=True),
        sa.CheckConstraint("home_team_id IS NOT NULL OR home_placeholder IS NOT NULL", name="chk_home_team"),
        sa.CheckConstraint("away_team_id IS NOT NULL OR away_placeholder IS NOT NULL", name="chk_away_team"),
        sa.CheckConstraint("advancing_team_id IS NULL OR stage != 'group'", name="chk_advancing_knockout"),
        sa.CheckConstraint("advancing_team_id IS NULL OR advancing_team_id = home_team_id OR advancing_team_id = away_team_id", name="chk_advancing_valid"),
        sa.CheckConstraint("(home_score IS NULL AND away_score IS NULL) OR (home_score IS NOT NULL AND away_score IS NOT NULL)", name="chk_scores_pair"),
        sa.CheckConstraint("(home_score IS NULL OR home_score >= 0) AND (away_score IS NULL OR away_score >= 0)", name="chk_scores_positive"),
        sa.CheckConstraint("submission_deadline <= match_date", name="chk_submission_deadline_before_match"),
    )
    op.create_index("idx_matches_stage", "matches", ["stage"])
    op.create_index("idx_matches_date", "matches", ["match_date"])
    op.create_index("idx_matches_status", "matches", ["status"])
    op.create_index("idx_matches_group", "matches", ["group_letter"])
    op.create_index("idx_matches_home_team", "matches", ["home_team_id"])
    op.create_index("idx_matches_away_team", "matches", ["away_team_id"])

    # PREDICTIONS
    op.create_table(
        "predictions",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_id", UUID(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("league_id", UUID(), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("advancing_team_id", UUID(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "match_id", "league_id"),
        sa.CheckConstraint("home_score >= 0 AND away_score >= 0", name="chk_pred_scores_positive"),
    )
    op.create_index("idx_predictions_user", "predictions", ["user_id"])
    op.create_index("idx_predictions_match", "predictions", ["match_id"])
    op.create_index("idx_predictions_league", "predictions", ["league_id"])
    op.create_index("idx_predictions_user_league", "predictions", ["user_id", "league_id"])

    # PREDICTION SCORES
    op.create_table(
        "prediction_scores",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("prediction_id", UUID(), sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("exact_score_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("outcome_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("group_position_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("exact_score_points IN (0, 3)", name="chk_exact_points"),
        sa.CheckConstraint("outcome_points IN (0, 1)", name="chk_outcome_points"),
        sa.CheckConstraint("group_position_points BETWEEN 0 AND 3", name="chk_group_points"),
        sa.CheckConstraint("total_points = exact_score_points + outcome_points + group_position_points", name="chk_total_points"),
    )
    op.create_index("idx_pred_scores_prediction", "prediction_scores", ["prediction_id"])

    # SPECIAL PREDICTIONS
    op.create_table(
        "special_predictions",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("league_id", UUID(), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("category", special_category, nullable=False),
        sa.Column("team_id", UUID(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("player_id", UUID(), sa.ForeignKey("players.id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "league_id", "category"),
        sa.CheckConstraint("team_id IS NOT NULL OR player_id IS NOT NULL", name="chk_special_target"),
        sa.CheckConstraint(
            "(category = 'champion' AND team_id IS NOT NULL AND player_id IS NULL) "
            "OR (category != 'champion' AND player_id IS NOT NULL AND team_id IS NULL)",
            name="chk_special_type",
        ),
    )
    op.create_index("idx_special_pred_user", "special_predictions", ["user_id"])
    op.create_index("idx_special_pred_league", "special_predictions", ["league_id"])
    op.create_index("idx_special_pred_user_league", "special_predictions", ["user_id", "league_id"])

    # SPECIAL RESULTS
    op.create_table(
        "special_results",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("category", special_category, nullable=False, unique=True),
        sa.Column("team_id", UUID(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("player_id", UUID(), sa.ForeignKey("players.id"), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("team_id IS NOT NULL OR player_id IS NOT NULL", name="chk_result_target"),
        sa.CheckConstraint(
            "(category = 'champion' AND team_id IS NOT NULL AND player_id IS NULL) "
            "OR (category != 'champion' AND player_id IS NOT NULL AND team_id IS NULL)",
            name="chk_result_type",
        ),
    )

    # SPECIAL PREDICTION SCORES
    op.create_table(
        "special_prediction_scores",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("special_prediction_id", UUID(), sa.ForeignKey("special_predictions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("points_awarded", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("points_awarded IN (0, 6)", name="chk_special_points"),
    )
    op.create_index("idx_special_prediction_scores_prediction", "special_prediction_scores", ["special_prediction_id"])

    # AUDIT LOG
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity", sa.String(100), nullable=False),
        sa.Column("entity_id", UUID(), nullable=True),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_audit_user", "audit_log", ["user_id"])
    op.create_index("idx_audit_entity", "audit_log", ["entity", "entity_id"])
    op.create_index("idx_audit_created", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("special_prediction_scores")
    op.drop_table("special_results")
    op.drop_table("special_predictions")
    op.drop_table("prediction_scores")
    op.drop_table("predictions")
    op.drop_table("matches")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("league_members")
    op.drop_table("leagues")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS special_category")
    op.execute("DROP TYPE IF EXISTS match_status")
    op.execute("DROP TYPE IF EXISTS match_stage")
    op.execute("DROP TYPE IF EXISTS player_position")
    op.execute("DROP TYPE IF EXISTS user_role")
