"""Sync Clash Royale cards from the official API into the local database.

Usage
-----
From the backend/ directory (with venv activated)::

    python -m scripts.sync_cards

Or with an explicit token override::

    CR_API_TOKEN=<token> python -m scripts.sync_cards

What it does
------------
1. Fetches GET https://api.clashroyale.com/v1/cards  (icon URLs, levels, rarity)
2. Fetches https://royaleapi.github.io/cr-api-data/json/cards.json
   (type, description, arena – fields absent from the official endpoint)
3. For each card in the response:
   - If the card already exists (matched by card_id) → updates every field in
     place so values always reflect the latest game patch.
   - If the card is new → inserts a fresh row.
4. Prints a summary: X inserted, Y updated, Z unchanged.

Re-run this script after every game patch to keep the cards table up to date.
"""

import asyncio
import logging
import sys

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
CR_API_DATA_URL = "https://royaleapi.github.io/cr-api-data/json/cards.json"


# ---------------------------------------------------------------------------
# API fetcher
# ---------------------------------------------------------------------------

async def fetch_cards(token: str) -> list[dict]:
    """Fetch the full card catalogue from the Clash Royale API.

    The official /cards endpoint only returns: id, name, iconUrls, maxLevel,
    elixirCost, rarity (and a few evolution fields). Fields like `type`,
    `description` and `arena` are **not** included – those come from the
    community data source fetched separately in fetch_community_data().

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


async def fetch_community_data() -> dict[int, dict]:
    """Fetch card metadata from the RoyaleAPI community data repository.

    This source provides fields absent from the official endpoint: type
    (Troop / Spell / Building), description, arena number.

    Returns:
        Dict mapping card_id (int) → community card dict.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        log.info("Fetching community card data from %s …", CR_API_DATA_URL)
        response = await client.get(CR_API_DATA_URL)
        response.raise_for_status()

    items: list[dict] = response.json()
    log.info("Received %d cards from community data.", len(items))
    return {item["id"]: item for item in items if "id" in item}


# ---------------------------------------------------------------------------
# Mapper  –  raw API dict + community dict  →  Card kwargs
# ---------------------------------------------------------------------------

def _map_api_card(raw: dict, community: dict) -> dict:
    """Convert one CR API card object to a dict of Card column values.

    Args:
        raw: Card dict from the official /v1/cards endpoint.
        community: Matching card dict from the RoyaleAPI community data
                   (provides type, description, arena).

    The full raw payload from the official API is preserved in raw_data.
    """
    icon_urls = raw.get("iconUrls") or {}

    return {
        "card_id": raw["id"],
        "name": raw.get("name", ""),
        "rarity": raw.get("rarity", ""),
        # 'type' is absent from the official endpoint – use community data.
        "card_type": community.get("type"),
        "elixir_cost": raw.get("elixirCost"),
        "max_level": raw.get("maxLevel", 0),
        "max_evolution_level": raw.get("maxEvolutionLevel"),
        # deployTime / speed are not in either source – left as None.
        "deploy_time": None,
        "speed": None,
        # 'arena' in community data is a bare int (arena number).
        "arena_id": community.get("arena"),
        # 'description' is absent from the official endpoint – use community data.
        "description": community.get("description"),
        "target": raw.get("target"),
        "icon_url_medium": icon_urls.get("medium"),
        "raw_data": raw,
    }


# ---------------------------------------------------------------------------
# Upsert logic
# ---------------------------------------------------------------------------

async def sync_cards(session: AsyncSession, raw_cards: list[dict], community_data: dict[int, dict]) -> dict[str, int]:
    """Upsert cards into the database.

    Args:
        session: Active async SQLAlchemy session.
        raw_cards: Raw card objects from the CR API.
        community_data: Community card data keyed by card_id.

    Returns:
        Dict with keys "inserted", "updated", "unchanged".
    """
    counters = {"inserted": 0, "updated": 0, "unchanged": 0}

    # Load all existing cards indexed by card_id for O(1) lookup
    result = await session.execute(select(Card))
    existing: dict[int, Card] = {c.card_id: c for c in result.scalars().all()}

    for raw in raw_cards:
        card_id: int = raw["id"]
        community = community_data.get(card_id, {})
        mapped = _map_api_card(raw, community)

        if card_id in existing:
            card = existing[card_id]
            changed = False

            for field, new_value in mapped.items():
                if getattr(card, field) != new_value:
                    setattr(card, field, new_value)
                    changed = True

            if changed:
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

    try:
        community_data = await fetch_community_data()
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not fetch community data (%s). type/description will be null.", exc)
        community_data = {}

    async with session_factory() as session:
        counters = await sync_cards(session, raw_cards, community_data)

    await engine.dispose()

    log.info(
        "Sync complete — inserted: %d | updated: %d | unchanged: %d",
        counters["inserted"],
        counters["updated"],
        counters["unchanged"],
    )


if __name__ == "__main__":
    asyncio.run(main())
