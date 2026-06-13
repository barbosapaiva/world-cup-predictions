"""
Sync match results from football-data.org API.

Checks the DB for matches that should have finished (match_date + 2h < now)
but are still marked as 'scheduled' or 'live'. If any exist, fetches results
from the API and updates status + scores only (via match_external_links).

After updating, recalculates prediction scores for affected matches.

Usage:
    python -m pipelines.football_data.sync_results
    python -m pipelines.football_data.sync_results --loop
"""

import argparse
import asyncio
import logging
from datetime import timedelta

from sqlalchemy import text

from pipelines.common.db import get_engine, get_session
from pipelines.football_data.client import FootballDataClient
from pipelines.football_data.load import PROVIDER
from pipelines.football_data.transform import STATUS_MAP

logger = logging.getLogger(__name__)

FINISH_BUFFER = timedelta(hours=2)
LOOP_INTERVAL = 300  # 5 minutes


# --- DB queries ---

FIND_PENDING = text("""
    SELECT m.id, mel.external_id, m.status::text, m.home_score, m.away_score
    FROM matches m
    JOIN match_external_links mel ON mel.match_id = m.id AND mel.provider = :provider
    WHERE m.status::text IN ('scheduled', 'live')
      AND m.match_date + interval '3 hours' < now()
    ORDER BY m.match_number
""")

UPDATE_MATCH_RESULT = text("""
    UPDATE matches
    SET status = CAST(:status AS match_status),
        home_score = :home_score,
        away_score = :away_score
    WHERE id = :match_id
""")

FIND_PREDICTIONS_FOR_MATCH = text("""
    SELECT p.id AS prediction_id,
           p.home_score AS pred_home,
           p.away_score AS pred_away
    FROM predictions p
    WHERE p.match_id = :match_id
""")

UPSERT_PREDICTION_SCORE = text("""

    INSERT INTO prediction_scores (
        prediction_id,
        exact_score_points,
        outcome_points,
        group_position_points,
        total_points
    )
    VALUES (:prediction_id, :exact, :outcome, 0, CAST(:exact AS int) + CAST(:outcome AS int))
    ON CONFLICT (prediction_id) DO UPDATE SET
        exact_score_points = EXCLUDED.exact_score_points,
        outcome_points = EXCLUDED.outcome_points,
        total_points = EXCLUDED.total_points
""")

EXACT_SCORE_POINTS = 3
OUTCOME_POINTS = 1


def calculate_points(pred_home: int, pred_away: int, real_home: int, real_away: int) -> tuple[int, int]:
    """Returns (exact_score_points, outcome_points)."""
    if pred_home == real_home and pred_away == real_away:
        return EXACT_SCORE_POINTS, 0

    pred_outcome = (pred_home > pred_away) - (pred_home < pred_away)
    real_outcome = (real_home > real_away) - (real_home < real_away)

    if pred_outcome == real_outcome:
        return 0, OUTCOME_POINTS

    return 0, 0


async def get_pending_matches() -> list[dict]:
    """Find matches that should have finished but haven't been updated."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(FIND_PENDING, {"provider": PROVIDER})
        rows = [dict(r._mapping) for r in result.fetchall()]
    await engine.dispose()
    return rows


async def sync_once() -> int:
    """Run one sync cycle. Returns number of matches updated."""
    pending = await get_pending_matches()
    if not pending:
        logger.info("No pending matches to sync.")
        return 0

    logger.info(
        "Found %d pending match(es) (external IDs: %s)",
        len(pending),
        ", ".join(row["external_id"] for row in pending),
    )

    client = FootballDataClient()
    updated = 0
    scored = 0

    async with get_session() as session:
        for db_row in pending:
            ext_id = db_row["external_id"]

            try:
                api_match = client.get(f"matches/{ext_id}")
            except Exception:
                logger.exception("Failed to fetch match %s from API", ext_id)
                continue

            new_status = STATUS_MAP.get(api_match["status"], "scheduled")
            ft = api_match.get("score", {}).get("fullTime", {})
            new_home = ft.get("home")
            new_away = ft.get("away")

            if new_status == "finished" and (new_home is None or new_away is None):
                logger.warning("Match %s finished but no scores yet, skipping", ext_id)
                continue

            if new_status != "finished":
                new_home = None
                new_away = None

            if new_status == db_row["status"] and new_home == db_row["home_score"] and new_away == db_row["away_score"]:
                continue

            match_id = db_row["id"]
            await session.execute(
                UPDATE_MATCH_RESULT,
                {"match_id": match_id, "status": new_status, "home_score": new_home, "away_score": new_away},
            )
            updated += 1

            home_name = api_match.get("homeTeam", {}).get("tla", "?")
            away_name = api_match.get("awayTeam", {}).get("tla", "?")
            score_str = f"{new_home}-{new_away}" if new_home is not None else "no score"
            logger.info("  Updated %s: %s vs %s → %s (%s)", ext_id, home_name, away_name, score_str, new_status)

            if new_status == "finished":
                result = await session.execute(FIND_PREDICTIONS_FOR_MATCH, {"match_id": match_id})
                predictions = result.fetchall()

                for pred in predictions:
                    exact, outcome = calculate_points(pred.pred_home, pred.pred_away, new_home, new_away)
                    await session.execute(
                        UPSERT_PREDICTION_SCORE,
                        {"prediction_id": pred.prediction_id, "exact": exact, "outcome": outcome},
                    )
                    scored += 1

                logger.info("    Scored %d prediction(s)", len(predictions))

    logger.info("Updated %d match(es), scored %d prediction(s).", updated, scored)
    return updated


async def loop():
    """Run sync every LOOP_INTERVAL seconds."""
    logger.info("Starting sync loop (every %ds)...", LOOP_INTERVAL)
    while True:
        try:
            await sync_once()
        except Exception:
            logger.exception("Sync error")
        await asyncio.sleep(LOOP_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description="Sync match results")
    parser.add_argument("--loop", action="store_true", help="Run continuously every 5 min")
    args = parser.parse_args()

    if args.loop:
        asyncio.run(loop())
    else:
        asyncio.run(sync_once())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )
    main()
