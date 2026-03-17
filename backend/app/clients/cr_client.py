"""Async client for the official Clash Royale API.

Only covers the player-profile endpoint used for on-demand lookups.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

log = logging.getLogger(__name__)

_BASE = "https://api.clashroyale.com/v1"


class CRApiError(Exception):
    """Raised when the CR API returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"CR API {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


async def fetch_player(tag: str, token: str) -> dict:
    """Fetch a single player profile from the CR API.

    Args:
        tag: Battle tag with or without leading ``#``.
        token: CR API bearer token.

    Returns:
        Raw player dict from the API (keys: tag, name, expLevel,
        trophies, bestTrophies, wins, losses, battleCount, currentDeck …).

    Raises:
        CRApiError: On 4xx / 5xx responses.
        httpx.RequestError: On network errors.
    """
    clean = tag.lstrip("#").upper()
    encoded = quote(f"#{clean}", safe="")  # → %23TAG
    url = f"{_BASE}/players/{encoded}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        log.info("CR API lookup: %s", url)
        resp = await client.get(url, headers=headers)

    if resp.status_code == 404:
        raise CRApiError(404, f"Player #{clean} not found in CR API.")
    if resp.status_code != 200:
        raise CRApiError(resp.status_code, resp.text[:200])

    return resp.json()
