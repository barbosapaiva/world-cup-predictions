"""
Transform raw football-data.org JSON → DB-ready DataFrames/CSVs.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")

# --- Mapping dictionaries ---

STAGE_MAP = {
    "GROUP_STAGE": "group",
    "ROUND_OF_32": "R32",
    "LAST_32": "R32",
    "LAST_16": "R16",
    "QUARTER_FINALS": "QF",
    "SEMI_FINALS": "SF",
    "THIRD_PLACE": "3rd",
    "FINAL": "F",
}

STATUS_MAP = {
    "TIMED": "scheduled",
    "SCHEDULED": "scheduled",
    "IN_PLAY": "live",
    "PAUSED": "live",
    "FINISHED": "finished",
    "POSTPONED": "scheduled",
    "CANCELLED": "scheduled",
    "SUSPENDED": "live",
}

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Defence": "DF",
    "Midfield": "MF",
    "Offence": "FW",
}

REGION_TO_CONFEDERATION = {
    "Europe": "UEFA",
    "South America": "CONMEBOL",
    "Africa": "CAF",
    "Asia": "AFC",
    "N/C America": "CONCACAF",
    "Oceania": "OFC",
}

CONFEDERATION_OVERRIDES = {
    "Australia": "AFC",
}

DEADLINE_OFFSET = timedelta(hours=1)


# --- Helpers ---


def _extract_group_letter(group_str: str | None) -> str | None:
    if not group_str:
        return None
    cleaned = group_str.split(" ")[-1] if " " in group_str else group_str.replace("GROUP_", "")
    return cleaned[-1] if len(cleaned) > 1 else cleaned


def _build_confederation_lookup(raw_areas: dict) -> dict[str, str]:
    lookup = {}
    for area in raw_areas.get("areas", []):
        country = area["name"]
        parent = area.get("parentArea")
        if country in CONFEDERATION_OVERRIDES:
            lookup[country] = CONFEDERATION_OVERRIDES[country]
        elif parent in REGION_TO_CONFEDERATION:
            lookup[country] = REGION_TO_CONFEDERATION[parent]
    return lookup


def _build_group_map(raw_standings: dict) -> dict[str, str]:
    group_map = {}
    for group in raw_standings.get("standings", []):
        letter = _extract_group_letter(group["group"])
        for entry in group["table"]:
            group_map[entry["team"]["tla"]] = letter
    return group_map


# --- Transform functions ---


def transform_teams(raw_teams: dict, raw_standings: dict | None, raw_areas: dict | None) -> pd.DataFrame:
    group_map = _build_group_map(raw_standings) if raw_standings else {}
    confed_lookup = _build_confederation_lookup(raw_areas) if raw_areas else {}

    rows = []
    for t in raw_teams["teams"]:
        tla = t["tla"]
        area_name = t.get("area", {}).get("name", "")
        rows.append(
            {
                "name": t["name"],
                "code": tla,
                "flag_url": t.get("crest"),
                "group_letter": group_map.get(tla),
                "confederation": confed_lookup.get(area_name),
            }
        )

    df = pd.DataFrame(rows)
    teams_with_group = df["group_letter"].notna().sum()
    teams_with_confed = df["confederation"].notna().sum()

    logger.info(
        "Teams: %s, with group: %s, with confed: %s",
        len(df),
        teams_with_group,
        teams_with_confed,
    )
    return df


def transform_matches(raw_matches: dict, raw_teams: dict) -> pd.DataFrame:
    api_id_to_tla = {t["id"]: t["tla"] for t in raw_teams["teams"]}

    rows = []
    for i, m in enumerate(raw_matches["matches"], start=1):
        stage_db = STAGE_MAP.get(m["stage"])
        if not stage_db:
            logger.warning(f"Unknown stage '{m['stage']}' in match {m['id']}, skipping")
            continue

        status_db = STATUS_MAP.get(m["status"], "scheduled")

        home_api_id = m.get("homeTeam", {}).get("id")
        away_api_id = m.get("awayTeam", {}).get("id")
        home_tla = api_id_to_tla.get(home_api_id) if home_api_id else None
        away_tla = api_id_to_tla.get(away_api_id) if away_api_id else None

        home_ph = None if home_tla else (m.get("homeTeam", {}).get("shortName") or "TBD")[:10]
        away_ph = None if away_tla else (m.get("awayTeam", {}).get("shortName") or "TBD")[:10]

        ft = m.get("score", {}).get("fullTime", {})
        home_score = ft.get("home") if status_db == "finished" else None
        away_score = ft.get("away") if status_db == "finished" else None

        match_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        deadline_dt = match_dt - DEADLINE_OFFSET

        rows.append(
            {
                "match_number": i,
                "stage": stage_db,
                "group_letter": _extract_group_letter(m.get("group")),
                "home_team_code": home_tla,
                "away_team_code": away_tla,
                "home_placeholder": home_ph,
                "away_placeholder": away_ph,
                "match_date": m["utcDate"],
                "submission_deadline": deadline_dt.isoformat(),
                "venue": m.get("venue"),
                "status": status_db,
                "home_score": home_score,
                "away_score": away_score,
            }
        )

    df = pd.DataFrame(rows)
    logger.info(f"Matches: {len(df)}")
    return df


def transform_players(raw_squads: dict) -> pd.DataFrame:
    rows = []
    skipped = 0

    for tla, team_data in raw_squads.items():
        for p in team_data["squad"]:
            position_db = POSITION_MAP.get(p.get("position"))
            if not position_db:
                skipped += 1
                continue
            rows.append(
                {
                    "team_code": tla,
                    "name": p["name"],
                    "position": position_db,
                    "birth_date": p.get("dateOfBirth"),
                }
            )

    df = pd.DataFrame(rows)
    logger.info(f"Players: {len(df)}, skipped: {skipped}")
    return df


# --- Run all transforms ---


def run() -> dict[str, pd.DataFrame]:
    raw_teams = json.load(open(DATA_RAW / "teams.json"))

    raw_standings = None
    if (DATA_RAW / "standings.json").exists():
        raw_standings = json.load(open(DATA_RAW / "standings.json"))

    raw_areas = None
    if (DATA_RAW / "areas.json").exists():
        raw_areas = json.load(open(DATA_RAW / "areas.json"))

    raw_matches = json.load(open(DATA_RAW / "matches.json"))

    result = {
        "teams": transform_teams(raw_teams, raw_standings, raw_areas),
        "matches": transform_matches(raw_matches, raw_teams),
    }

    if (DATA_RAW / "squads.json").exists():
        raw_squads = json.load(open(DATA_RAW / "squads.json"))
        result["players"] = transform_players(raw_squads)

    # Save CSVs
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, df in result.items():
        df.to_csv(DATA_PROCESSED / f"{name}.csv", index=False)
        logger.info(f"Saved {name}.csv")

    return result
