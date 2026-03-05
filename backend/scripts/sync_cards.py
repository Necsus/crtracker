"""Sync Clash Royale cards from the official API into the local database.

Usage
-----
From the backend/ directory (with venv activated):

    python -m scripts.sync_cards

Or with an explicit token override:

    CR_API_TOKEN=<token> python -m scripts.sync_cards

What it does
------------
1. Fetches GET https://api.clashroyale.com/v1/cards
2. For each card in the response:
   - If the card already exists (matched by card_id) → updates every field in
     place so values always reflect the latest game patch.
   - If the card is new → inserts a fresh row.
3. Prints a summary: X inserted, Y updated, Z unchanged.

Re-run this script after every game patch to keep the cards table up to date.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Bootstrap – make sure the app package is importable when running as a script
# ---------------------------------------------------------------------------
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.b_models.card import Card  # noqa: E402
from app.database import Base  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

CR_CARDS_URL = "https://api.clashroyale.com/v1/cards"


# ---------------------------------------------------------------------------
# API fetcher
# ---------------------------------------------------------------------------

async def fetch_cards(token: str) -> list[dict]:
    """Fetch the full card catalogue from the Clash Royale API.

    Args:
        token: Bearer token for the CR API.

    Returns:
        List of raw card dicts from the API response.

    Raises:
        httpx.HTTPStatusError: If the API returns a non-2xx response.
        ValueError: If the response format is unexpected.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        log.info("Fetching cards from %s …", CR_CARDS_URL)
        response = await client.get(CR_CARDS_URL, headers=headers)
        response.raise_for_status()

    data = response.json()
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError(f"Unexpected API response format: {data}")

    log.info("Received %d cards from the API.", len(items))
    return items


# ---------------------------------------------------------------------------
# Mapper  –  raw API dict  →  Card kwargs
# ---------------------------------------------------------------------------

def _map_api_card(raw: dict) -> dict:
    """Convert one CR API card object to a dict of Card column values.

    The full raw payload is also preserved in raw_data.
    """
    icon_urls = raw.get("iconUrls") or {}

    return {
        "card_id": raw["id"],
        "name": raw.get("name", ""),
        "rarity": raw.get("rarity", ""),
        "card_type": raw.get("type"),
        "elixir_cost": raw.get("elixirCost"),
        "max_level": raw.get("maxLevel", 0),
        "max_evolution_level": raw.get("maxEvolutionLevel"),
        "deploy_time": raw.get("deployTime"),
        "speed": raw.get("speed"),
        "arena_id": raw.get("arenaId"),
        "description": raw.get("description"),
        "target": raw.get("target"),
        "icon_url_medium": icon_urls.get("medium"),
        "raw_data": raw,
    }


# ---------------------------------------------------------------------------
# Upsert logic
# ---------------------------------------------------------------------------

async def sync_cards(session: AsyncSession, raw_cards: list[dict]) -> dict[str, int]:
    """Upsert cards into the database.

    Args:
        session: Active async SQLAlchemy session.
        raw_cards: Raw card objects from the CR API.

    Returns:
        Dict with keys "inserted", "updated", "unchanged".
    """
    now = datetime.now(tz=timezone.utc)
    counters = {"inserted": 0, "updated": 0, "unchanged": 0}

    # Load all existing cards indexed by card_id for O(1) lookup
    result = await session.execute(select(Card))
    existing: dict[int, Card] = {c.card_id: c for c in result.scalars().all()}

    for raw in raw_cards:
        mapped = _map_api_card(raw)
        card_id: int = mapped["card_id"]

        if card_id in existing:
            card = existing[card_id]
            changed = False

            for field, new_value in mapped.items():
                if getattr(card, field) != new_value:
                    setattr(card, field, new_value)
                    changed = True

            if changed:
                card.updated_at = now
                counters["updated"] += 1
            else:
                counters["unchanged"] += 1
        else:
            new_card = Card(**mapped)
            session.add(new_card)
            counters["inserted"] += 1

    await session.commit()
    return counters


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    settings = get_settings()

    if not settings.cr_api_token:
        log.error(
            "CR_API_TOKEN is not set. "
            "Get a token at https://developer.clashroyale.com and set it in .env"
        )
        sys.exit(1)

    # Use synchronous (non-async) DB URL variant derived from settings
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        raw_cards = await fetch_cards(settings.cr_api_token)
    except httpx.HTTPStatusError as exc:
        log.error("CR API error %s: %s", exc.response.status_code, exc.response.text)
        await engine.dispose()
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        log.error("Failed to fetch cards: %s", exc)
        await engine.dispose()
        sys.exit(1)

    async with session_factory() as session:
        counters = await sync_cards(session, raw_cards)

    await engine.dispose()

    log.info(
        "Sync complete — inserted: %d | updated: %d | unchanged: %d",
        counters["inserted"],
        counters["updated"],
        counters["unchanged"],
    )


if __name__ == "__main__":
    asyncio.run(main())
