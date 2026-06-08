"""
Football Data pipeline: Extract → Transform → Load.

Source: football-data.org API
Target: PostgreSQL (teams, matches, players)

Usage:
    python -m pipelines.football_data.run
    python -m pipelines.football_data.run --skip-extract
    python -m pipelines.football_data.run --skip-squads
    python -m pipelines.football_data.run --skip-load
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()  # loads .env in dev; no-op if file missing
except ImportError:
    pass  # python-dotenv not installed (e.g. production) — env vars come from the system

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Football Data pipeline")
    parser.add_argument("--skip-extract", action="store_true", help="Use existing raw files")
    parser.add_argument("--skip-squads", action="store_true", help="Skip squad extraction (slow)")
    parser.add_argument("--skip-load", action="store_true", help="Extract + transform only")
    parser.add_argument("--competition", default=os.getenv("FOOTBALL_DATA_COMPETITION"), help="Competition code")
    return parser.parse_args()


async def main():
    args = parse_args()

    # --- EXTRACT ---
    if not args.skip_extract:
        logger.info("=" * 50)
        logger.info("EXTRACT")
        logger.info("=" * 50)
        from pipelines.football_data.extract import run as extract_run

        extract_run(competition=args.competition, skip_squads=args.skip_squads)
    else:
        logger.info("Skipping extract (using existing raw files)")
        raw = Path("data/raw")
        for f in ["teams.json", "matches.json"]:
            if not (raw / f).exists():
                logger.error(f"Missing {raw / f} — run without --skip-extract first")
                sys.exit(1)

    # --- TRANSFORM ---
    logger.info("=" * 50)
    logger.info("TRANSFORM")
    logger.info("=" * 50)
    from pipelines.football_data.transform import run as transform_run

    data = transform_run()

    # --- LOAD ---
    if not args.skip_load:
        logger.info("=" * 50)
        logger.info("LOAD")
        logger.info("=" * 50)
        from pipelines.football_data.load import load_matches, load_players, load_teams

        await load_teams(data["teams"])
        await load_matches(data["matches"])

        if "players" in data:
            await load_players(data["players"])
    else:
        logger.info("Skipping load (--skip-load)")

    logger.info("=" * 50)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 50)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )
    asyncio.run(main())
