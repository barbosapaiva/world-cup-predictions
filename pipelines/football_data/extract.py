"""
Extract data from football-data.org API → data/raw/ JSON files.
"""

import json
import logging
import os
import time
from pathlib import Path

from pipelines.football_data.client import FootballDataClient

logger = logging.getLogger(__name__)

DATA_RAW = Path("data/raw")


def save_raw(data: dict | list, filename: str) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    path = DATA_RAW / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {path} ({path.stat().st_size / 1024:.1f} KB)")
    return path


def extract_competition(client: FootballDataClient, competition: str) -> dict:
    logger.info(f"Extracting competition: {competition}")
    data = client.get(f"competitions/{competition}")
    save_raw(data, "competition.json")
    return data


def extract_teams(client: FootballDataClient, competition: str) -> dict:
    logger.info(f"Extracting teams: {competition}")
    data = client.get(f"competitions/{competition}/teams")
    save_raw(data, "teams.json")
    logger.info(f"Teams: {data['count']}")
    return data


def extract_standings(client: FootballDataClient, competition: str) -> dict | None:
    logger.info(f"Extracting standings: {competition}")
    try:
        data = client.get(f"competitions/{competition}/standings")
        save_raw(data, "standings.json")
        logger.info(f"Groups: {len(data.get('standings', []))}")
        return data
    except Exception as e:
        logger.warning(f"Standings not available: {e}")
        return None


def extract_matches(client: FootballDataClient, competition: str) -> dict:
    logger.info(f"Extracting matches: {competition}")
    data = client.get(f"competitions/{competition}/matches")
    save_raw(data, "matches.json")
    logger.info(f"Matches: {data['resultSet']['count']}")
    return data


def extract_areas(client: FootballDataClient) -> dict:
    logger.info("Extracting areas")
    data = client.get("areas")
    save_raw(data, "areas.json")
    logger.info(f"Areas: {data['count']}")
    return data


def extract_squads(client: FootballDataClient, teams: list[dict]) -> dict:
    """Fetch squad for each team. Rate limited (~7s between calls)."""
    logger.info(f"Extracting squads for {len(teams)} teams (~{len(teams) * 7 / 60:.0f} min)")
    squads = {}

    for i, team in enumerate(teams):
        tid, tla = team["id"], team["tla"]
        if i > 0:
            time.sleep(7)

        detail = client.get(f"teams/{tid}")
        squad = detail.get("squad", [])
        squads[tla] = {
            "team_id": tid,
            "team_tla": tla,
            "team_name": detail["name"],
            "squad": squad,
        }
        logger.info(f"  [{i + 1}/{len(teams)}] {tla}: {len(squad)} players")

    save_raw(squads, "squads.json")
    total = sum(len(s["squad"]) for s in squads.values())
    logger.info(f"Total players: {total}")
    return squads


def run(competition: str = os.getenv("FOOTBALL_DATA_COMPETITION"), skip_squads: bool = False) -> dict:
    client = FootballDataClient()

    result = {
        "competition": extract_competition(client, competition),
        "teams": extract_teams(client, competition),
        "standings": extract_standings(client, competition),
        "matches": extract_matches(client, competition),
        "areas": extract_areas(client),
    }

    if not skip_squads:
        result["squads"] = extract_squads(client, result["teams"]["teams"])
    else:
        logger.info("Skipping squads extraction")

    return result
