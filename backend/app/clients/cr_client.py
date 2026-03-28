"""Clash Royale official API client."""

import urllib.parse

import httpx


class CRApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"CR API {status_code}: {message}")


_BASE_URL = "https://api.clashroyale.com/v1"


def _encode_tag(tag: str) -> str:
    """Normalize tag (strip #) and URL-encode it for CR API paths."""
    normalized = tag.strip().upper().lstrip("#")
    return urllib.parse.quote(f"#{normalized}", safe="")


async def fetch_player(tag: str, token: str) -> dict:
    """Fetch a single player by tag from the CR API."""
    url = f"{_BASE_URL}/players/{_encode_tag(tag)}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        raise CRApiError(resp.status_code, resp.text[:200])
    return resp.json()


async def fetch_battles(tag: str, token: str) -> list[dict]:
    """Fetch the battlelog for a player from the CR API."""
    url = f"{_BASE_URL}/players/{_encode_tag(tag)}/battlelog"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        raise CRApiError(resp.status_code, resp.text[:200])
    return resp.json()  # returns a list of battle dicts
