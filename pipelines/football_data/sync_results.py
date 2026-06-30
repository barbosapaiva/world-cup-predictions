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
    SELECT m.id, mel.external_id, m.status::text, m.home_score, m.away_score,
           m.home_team_id, m.away_team_id, m.stage
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
        away_score = :away_score,
        advancing_team_id = :advancing_team_id
    WHERE id = :match_id
""")

FIND_PREDICTIONS_FOR_MATCH = text("""
    SELECT p.id AS prediction_id,
           p.home_score AS pred_home,
           p.away_score AS pred_away,
           p.advancing_team_id AS pred_advancing
    FROM predictions p
    WHERE p.match_id = :match_id
""")

UPSERT_PREDICTION_SCORE = text("""
    INSERT INTO prediction_scores (
        prediction_id,
        exact_score_points,
        outcome_points,
        advancing_team_points,
        group_position_points,
        total_points
    )
    VALUES (
        :prediction_id, :exact, :outcome, :advancing, 0,
        CAST(:exact AS int) + CAST(:outcome AS int) + CAST(:advancing AS int)
    )
    ON CONFLICT (prediction_id) DO UPDATE SET
        exact_score_points = EXCLUDED.exact_score_points,
        outcome_points = EXCLUDED.outcome_points,
        advancing_team_points = EXCLUDED.advancing_team_points,
        total_points = EXCLUDED.total_points
""")

FIND_KNOCKOUT_PLACEHOLDERS = text("""
    SELECT m.id, mel.external_id, m.home_placeholder, m.away_placeholder
    FROM matches m
    JOIN match_external_links mel ON mel.match_id = m.id AND mel.provider = :provider
    WHERE m.stage != 'group'
      AND (m.home_team_id IS NULL OR m.away_team_id IS NULL)
    ORDER BY m.match_number
""")

UPDATE_KNOCKOUT_HOME = text("""
    UPDATE matches
    SET home_team_id = (SELECT id FROM teams WHERE code = :home_code),
        home_placeholder = NULL
    WHERE id = :match_id AND home_team_id IS NULL
""")

UPDATE_KNOCKOUT_AWAY = text("""
    UPDATE matches
    SET away_team_id = (SELECT id FROM teams WHERE code = :away_code),
        away_placeholder = NULL
    WHERE id = :match_id AND away_team_id IS NULL
""")

FIND_COMPLETED_GROUPS = text("""
    SELECT m.group_letter, COUNT(*) AS finished
    FROM matches m
    WHERE m.stage = 'group' AND m.status::text = 'finished'
      AND m.group_letter IS NOT NULL
    GROUP BY m.group_letter
    HAVING COUNT(*) = (
        SELECT COUNT(*) FROM matches m2
        WHERE m2.stage = 'group' AND m2.group_letter = m.group_letter
    )
""")

FIND_UNSCORED_GROUP_PREDICTIONS = text("""
    SELECT gp.id, gp.league_id, gp.group_letter,
           gp.first_team_id, gp.second_team_id, gp.third_team_id, gp.fourth_team_id
    FROM group_predictions gp
    WHERE gp.group_letter = :group_letter AND gp.points_awarded IS NULL
""")

FIND_GROUP_STANDINGS = text("""
    SELECT m.home_team_id, m.away_team_id, m.home_score, m.away_score
    FROM matches m
    WHERE m.stage = 'group' AND m.group_letter = :group_letter
      AND m.status::text = 'finished'
""")

UPDATE_GROUP_PREDICTION_POINTS = text("""
    UPDATE group_predictions SET points_awarded = :points WHERE id = :pred_id
""")

EXACT_SCORE_POINTS = 3
OUTCOME_POINTS = 1
ADVANCING_TEAM_POINTS = 1


def calculate_points(
    pred_home: int,
    pred_away: int,
    real_home: int,
    real_away: int,
    pred_advancing: str | None = None,
    real_advancing: str | None = None,
) -> tuple[int, int, int]:
    """Returns (exact_score_points, outcome_points, advancing_team_points)."""
    # Advancing team bonus: only applies when both sides predicted/had a draw
    advancing = 0
    if (
        pred_advancing
        and real_advancing
        and pred_home == pred_away  # user predicted draw
        and real_home == real_away  # actual result was draw (90 min)
        and str(pred_advancing) == str(real_advancing)
    ):
        advancing = ADVANCING_TEAM_POINTS

    if pred_home == real_home and pred_away == real_away:
        return EXACT_SCORE_POINTS, 0, advancing

    pred_outcome = (pred_home > pred_away) - (pred_home < pred_away)
    real_outcome = (real_home > real_away) - (real_home < real_away)

    if pred_outcome == real_outcome:
        return 0, OUTCOME_POINTS, advancing

    return 0, 0, 0


async def get_pending_matches() -> list[dict]:
    """Find matches that should have finished but haven't been updated."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(FIND_PENDING, {"provider": PROVIDER})
        rows = [dict(r._mapping) for r in result.fetchall()]
    await engine.dispose()
    return rows


async def sync_once() -> int:
    """Run one sync cycle. Returns number of matches updated + knockout teams assigned."""
    client = FootballDataClient()

    # --- 1. Update match results ---
    pending = await get_pending_matches()
    updated = 0
    scored = 0

    if not pending:
        logger.info("No pending matches to sync.")
        return 0
    else:
        logger.info(
            "Found %d pending match(es) (external IDs: %s)",
            len(pending),
            ", ".join(row["external_id"] for row in pending),
        )

        async with get_session() as session:
            for db_row in pending:
                ext_id = db_row["external_id"]

                try:
                    api_match = client.get(f"matches/{ext_id}")
                except Exception:
                    logger.exception("Failed to fetch match %s from API", ext_id)
                    continue

                new_status = STATUS_MAP.get(api_match["status"], "scheduled")
                score_data = api_match.get("score", {})
                duration = score_data.get("duration", "REGULAR")

                # Use regularTime (90 min) when available, otherwise fullTime
                # regularTime only exists when duration is EXTRA_TIME or PENALTY_SHOOTOUT
                if duration in ("EXTRA_TIME", "PENALTY_SHOOTOUT") and score_data.get("regularTime"):
                    rt = score_data["regularTime"]
                    new_home = rt.get("home")
                    new_away = rt.get("away")
                else:
                    ft = score_data.get("fullTime", {})
                    new_home = ft.get("home")
                    new_away = ft.get("away")

                if new_status == "finished" and (new_home is None or new_away is None):
                    logger.warning("Match %s finished but no scores yet, skipping", ext_id)
                    continue

                # Determine advancing team (knockout only — group has check constraint)
                advancing_team_id = None
                if new_status == "finished" and db_row.get("stage") != "group":
                    winner = score_data.get("winner")
                    if winner == "HOME_TEAM":
                        advancing_team_id = db_row.get("home_team_id")
                    elif winner == "AWAY_TEAM":
                        advancing_team_id = db_row.get("away_team_id")

                if new_status != "finished":
                    new_home = None
                    new_away = None

                if new_status == db_row["status"] and new_home == db_row["home_score"] and new_away == db_row["away_score"]:
                    continue

                match_id = db_row["id"]
                await session.execute(
                    UPDATE_MATCH_RESULT,
                    {
                        "match_id": match_id,
                        "status": new_status,
                        "home_score": new_home,
                        "away_score": new_away,
                        "advancing_team_id": advancing_team_id,
                    },
                )
                updated += 1

                home_name = api_match.get("homeTeam", {}).get("tla", "?")
                away_name = api_match.get("awayTeam", {}).get("tla", "?")
                score_str = f"{new_home}-{new_away}" if new_home is not None else "no score"
                duration_str = f" ({duration})" if duration != "REGULAR" else ""
                logger.info("  Updated %s: %s vs %s → %s (%s%s)", ext_id, home_name, away_name, score_str, new_status, duration_str)

                if new_status == "finished":
                    result = await session.execute(FIND_PREDICTIONS_FOR_MATCH, {"match_id": match_id})
                    predictions = result.fetchall()

                    for pred in predictions:
                        exact, outcome, advancing = calculate_points(
                            pred.pred_home, pred.pred_away,
                            new_home, new_away,
                            pred_advancing=str(pred.pred_advancing) if pred.pred_advancing else None,
                            real_advancing=str(advancing_team_id) if advancing_team_id else None,
                        )
                        await session.execute(
                            UPSERT_PREDICTION_SCORE,
                            {"prediction_id": pred.prediction_id, "exact": exact, "outcome": outcome, "advancing": advancing},
                        )
                        scored += 1

                    logger.info("    Scored %d prediction(s)", len(predictions))

        logger.info("Updated %d match(es), scored %d prediction(s).", updated, scored)

    assigned = await sync_knockout_teams(client)

    logger.info("Sync complete: %d result(s), %d scored, %d knockout assignment(s).", updated, scored, assigned)
    return updated + assigned


def compute_group_standings(match_rows: list[dict]) -> list:
    """Compute group standings from match results. Returns list of team_ids in order."""
    stats: dict[str, dict] = {}

    for m in match_rows:
        h_id, a_id = str(m["home_team_id"]), str(m["away_team_id"])
        h_score, a_score = m["home_score"], m["away_score"]

        for tid in (h_id, a_id):
            if tid not in stats:
                stats[tid] = {"id": tid, "pts": 0, "gd": 0, "gf": 0}

        stats[h_id]["gf"] += h_score
        stats[h_id]["gd"] += h_score - a_score
        stats[a_id]["gf"] += a_score
        stats[a_id]["gd"] += a_score - h_score

        if h_score > a_score:
            stats[h_id]["pts"] += 3
        elif h_score < a_score:
            stats[a_id]["pts"] += 3
        else:
            stats[h_id]["pts"] += 1
            stats[a_id]["pts"] += 1

    ranked = sorted(stats.values(), key=lambda s: (-s["pts"], -s["gd"], -s["gf"]))
    return [r["id"] for r in ranked]


async def score_completed_groups() -> int:
    """Score group predictions for groups where all matches are finished."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(FIND_COMPLETED_GROUPS)
        completed = [dict(r._mapping) for r in result.fetchall()]
    await engine.dispose()

    if not completed:
        logger.info("No completed groups to score.")
        return 0

    total_scored = 0

    async with get_session() as session:
        for row in completed:
            group = row["group_letter"]

            # Get unscored predictions for this group
            result = await session.execute(FIND_UNSCORED_GROUP_PREDICTIONS, {"group_letter": group})
            predictions = [dict(r._mapping) for r in result.fetchall()]

            if not predictions:
                continue

            # Get actual standings
            result = await session.execute(FIND_GROUP_STANDINGS, {"group_letter": group})
            match_rows = [dict(r._mapping) for r in result.fetchall()]
            actual_order = compute_group_standings(match_rows)

            for pred in predictions:
                predicted_order = [
                    str(pred["first_team_id"]),
                    str(pred["second_team_id"]),
                    str(pred["third_team_id"]),
                    str(pred["fourth_team_id"]),
                ]
                points = sum(1 for p, a in zip(predicted_order, actual_order) if p == a)
                await session.execute(
                    UPDATE_GROUP_PREDICTION_POINTS,
                    {"pred_id": pred["id"], "points": points},
                )
                total_scored += 1

            logger.info("  Group %s: scored %d prediction(s) (standings: %s)", group, len(predictions), actual_order[:2])

    logger.info("Scored %d group prediction(s).", total_scored)
    return total_scored


async def sync_knockout_teams(client: FootballDataClient) -> int:
    """Check knockout matches with placeholders and assign teams if the API already knows them."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(FIND_KNOCKOUT_PLACEHOLDERS, {"provider": PROVIDER})
        placeholder_matches = [dict(r._mapping) for r in result.fetchall()]
    await engine.dispose()

    if not placeholder_matches:
        logger.info("No knockout matches with placeholders.")
        return 0

    logger.info("Found %d knockout match(es) with placeholders.", len(placeholder_matches))
    assigned = 0

    async with get_session() as session:
        for db_row in placeholder_matches:
            ext_id = db_row["external_id"]

            try:
                api_match = client.get(f"matches/{ext_id}")
            except Exception:
                logger.exception("Failed to fetch knockout match %s", ext_id)
                continue

            home_team = api_match.get("homeTeam", {})
            away_team = api_match.get("awayTeam", {})
            home_tla = home_team.get("tla") if home_team.get("id") else None
            away_tla = away_team.get("tla") if away_team.get("id") else None

            if not home_tla and not away_tla:
                continue

            match_id = db_row["id"]
            parts = []

            if home_tla and db_row["home_placeholder"] is not None:
                await session.execute(UPDATE_KNOCKOUT_HOME, {"match_id": match_id, "home_code": home_tla})
                parts.append(home_tla)

            if away_tla and db_row["away_placeholder"] is not None:
                await session.execute(UPDATE_KNOCKOUT_AWAY, {"match_id": match_id, "away_code": away_tla})
                parts.append(away_tla)

            if parts:
                assigned += 1
                logger.info("  Assigned knockout match %s: %s", ext_id, " vs ".join(parts))

    logger.info("Assigned teams for %d knockout match(es).", assigned)
    return assigned


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
    parser.add_argument("--score-groups", action="store_true", help="Score completed group predictions and exit")
    args = parser.parse_args()

    if args.score_groups:
        asyncio.run(score_completed_groups())
    elif args.loop:
        asyncio.run(loop())
    else:
        asyncio.run(sync_once())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )
    main()
