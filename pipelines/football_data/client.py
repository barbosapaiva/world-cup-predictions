"""
HTTP client for football-data.org API (v4).

Usage:
    from pipelines.football_data.client import FootballDataClient

    client = FootballDataClient()
    teams = client.get_teams(os.getenv("FOOTBALL_DATA_COMPETITION"))
"""

import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("FOOTBALL_DATA_API_BASE_URL")

# Free tier: 10 requests/minute
RATE_LIMIT_DELAY = 6.5


class FootballDataClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_TOKEN")
        if not self.api_key:
            raise ValueError("FOOTBALL_DATA_API_TOKEN not set")
        self.session = requests.Session()
        self.session.headers["X-Auth-Token"] = self.api_key
        self._last_call: float = 0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < RATE_LIMIT_DELAY:
            wait = RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            time.sleep(wait)
        self._last_call = time.time()

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        self._rate_limit()
        url = f"{BASE_URL}/{endpoint}"
        logger.info(f"GET {url}")
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
