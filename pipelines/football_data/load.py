"""
Load transformed data into PostgreSQL (upsert).
"""

import logging
from datetime import date, datetime

import pandas as pd
from sqlalchemy import text

from pipelines.common.db import get_session

logger = logging.getLogger(__name__)

PROVIDER = "football-data.org"

# --- SQL statements ---

UPSERT_TEAM = text("""
    INSERT INTO teams (name, code, flag_url, group_letter, confederation)
    VALUES (:name, :code, :flag_url, :group_letter, :confederation)
    ON CONFLICT (code) DO UPDATE SET
        name = EXCLUDED.name,
        flag_url = EXCLUDED.flag_url,
        group_letter = EXCLUDED.group_letter,
        confederation = EXCLUDED.confederation
""")

UPSERT_MATCH = text("""
    INSERT INTO matches (
        match_number, stage, group_letter,
        home_team_id, away_team_id,
        home_placeholder, away_placeholder,
        match_date, submission_deadline, venue,
        status, home_score, away_score
    )
    VALUES (
        :match_number, CAST(:stage AS match_stage), :group_letter,
        (SELECT id FROM teams WHERE code = :home_team_code),
        (SELECT id FROM teams WHERE code = :away_team_code),
        :home_placeholder, :away_placeholder,
        CAST(:match_date AS timestamptz), CAST(:submission_deadline AS timestamptz), :venue,
        CAST(:status AS match_status), :home_score, :away_score
    )
    ON CONFLICT (match_number) DO UPDATE SET
        stage = EXCLUDED.stage,
        group_letter = EXCLUDED.group_letter,
        home_team_id = EXCLUDED.home_team_id,
        away_team_id = EXCLUDED.away_team_id,
        home_placeholder = EXCLUDED.home_placeholder,
        away_placeholder = EXCLUDED.away_placeholder,
        match_date = EXCLUDED.match_date,
        submission_deadline = EXCLUDED.submission_deadline,
        venue = EXCLUDED.venue,
        status = EXCLUDED.status,
        home_score = EXCLUDED.home_score,
        away_score = EXCLUDED.away_score
    RETURNING id
""")

UPSERT_EXTERNAL_LINK = text("""
    INSERT INTO match_external_links (match_id, provider, external_id)
    VALUES (:match_id, :provider, :external_id)
    ON CONFLICT (match_id, provider) DO UPDATE SET
        external_id = EXCLUDED.external_id
""")

FIND_PLAYER = text("""
    SELECT id FROM players
    WHERE team_id = (SELECT id FROM teams WHERE code = :team_code)
      AND name = :name
""")

INSERT_PLAYER = text("""
    INSERT INTO players (team_id, name, position, birth_date)
    VALUES (
        (SELECT id FROM teams WHERE code = :team_code),
        :name, CAST(:position AS player_position), :birth_date
    )
""")

UPDATE_PLAYER = text("""
    UPDATE players SET
        position = CAST(:position AS player_position),
        birth_date = :birth_date
    WHERE id = :player_id
""")


def _nan_to_none(val):
    if pd.isna(val):
        return None
    return val


def _parse_datetime(val):
    val = _nan_to_none(val)
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(str(val).replace("Z", "+00:00"))


def _parse_int(val):
    val = _nan_to_none(val)
    if val is None:
        return None
    return int(val)


def _parse_date(val):
    val = _nan_to_none(val)
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val))


# --- Load functions ---


async def load_teams(df: pd.DataFrame) -> int:
    count = 0
    async with get_session() as session:
        for _, row in df.iterrows():
            await session.execute(
                UPSERT_TEAM,
                {
                    "name": row["name"],
                    "code": row["code"],
                    "flag_url": _nan_to_none(row.get("flag_url")),
                    "group_letter": _nan_to_none(row.get("group_letter")),
                    "confederation": _nan_to_none(row.get("confederation")),
                },
            )
            count += 1
    logger.info("Upserted %s teams", count)
    return count


async def load_matches(df: pd.DataFrame) -> int:
    """Upsert matches (ON CONFLICT match_number) + upsert external links."""
    count = 0
    async with get_session() as session:
        for _, row in df.iterrows():
            result = await session.execute(
                UPSERT_MATCH,
                {
                    "match_number": int(row["match_number"]),
                    "stage": row["stage"],
                    "group_letter": _nan_to_none(row.get("group_letter")),
                    "home_team_code": _nan_to_none(row.get("home_team_code")),
                    "away_team_code": _nan_to_none(row.get("away_team_code")),
                    "home_placeholder": _nan_to_none(row.get("home_placeholder")),
                    "away_placeholder": _nan_to_none(row.get("away_placeholder")),
                    "match_date": _parse_datetime(row["match_date"]),
                    "submission_deadline": _parse_datetime(row["submission_deadline"]),
                    "venue": _nan_to_none(row.get("venue")),
                    "status": row["status"],
                    "home_score": _parse_int(row.get("home_score")),
                    "away_score": _parse_int(row.get("away_score")),
                },
            )
            match_id = result.scalar_one()

            external_id = _parse_int(row.get("external_match_id"))
            if external_id is not None:
                await session.execute(
                    UPSERT_EXTERNAL_LINK,
                    {
                        "match_id": match_id,
                        "provider": PROVIDER,
                        "external_id": str(external_id),
                    },
                )

            count += 1

    logger.info("Upserted %s matches + external links (%s)", count, PROVIDER)
    return count


async def load_players(df: pd.DataFrame) -> dict:
    inserted = 0
    updated = 0

    async with get_session() as session:
        for _, row in df.iterrows():
            result = await session.execute(
                FIND_PLAYER,
                {
                    "team_code": row["team_code"],
                    "name": row["name"],
                },
            )
            existing = result.scalar_one_or_none()

            if existing:
                await session.execute(
                    UPDATE_PLAYER,
                    {
                        "player_id": existing,
                        "position": row["position"],
                        "birth_date": _parse_date(row.get("birth_date")),
                    },
                )
                updated += 1
            else:
                await session.execute(
                    INSERT_PLAYER,
                    {
                        "team_code": row["team_code"],
                        "name": row["name"],
                        "position": row["position"],
                        "birth_date": _parse_date(row.get("birth_date")),
                    },
                )
                inserted += 1

    logger.info("Players: %s inserted, %s updated", inserted, updated)
    return {"inserted": inserted, "updated": updated}
