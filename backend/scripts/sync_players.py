"""Sync Clash Royale Path of Legend top players into the local database.

Usage
-----
From the backend/ directory (with venv activated)::

    # Fetch the top 1000 players for the current season
    python -m scripts.sync_players

    # Custom top size
    python -m scripts.sync_players --top 200

    # Specific season (format YYYY-MM, defaults to current month)
    python -m scripts.sync_players --top 1000 --season 2026-02

    # Control concurrency (default: 10)
    python -m scripts.sync_players --concurrency 5

What it does
------------
1.  Fetches ``GET /v1/locations/global/pathoflegend/{season}/rankings/players?limit=N``
    to obtain the global Path of Legend leaderboard (rank + tag + name + leagueNumber).
2.  For each player tag, fetches the full profile via
    ``GET /v1/players/{tag}`` to get trophies, wins, losses, current deck, etc.
3.  Upserts each player into the ``players`` table with ``ON CONFLICT (tag) DO UPDATE``
    so the row is refreshed on every run.
4.  Prints a final summary.

Rate limiting
-------------
The CR API allows ~100 requests/minute per IP.  A semaphore (``--concurrency``,
default 10) and exponential back-off on 429 responses keep the script well
within the limit.
"""

import argparse
import asyncio
import logging
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Bootstrap – make sure the app package is importable when running as a script
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(ROOT))

from app.b_models.player import Player  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import Base  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

CR_API_BASE = "https://api.clashroyale.com/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_season() -> str:
    """Return the current season in YYYY-MM format (today's month)."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m")


def _previous_season(season: str) -> str:
    """Return the season one month before the given YYYY-MM season."""
    year, month = int(season[:4]), int(season[5:7])
    first_of_month = datetime(year, month, 1)
    prev = first_of_month - timedelta(days=1)
    return prev.strftime("%Y-%m")


# ---------------------------------------------------------------------------
# CR API client with retry / back-off
# ---------------------------------------------------------------------------

async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
    *,
    max_retries: int = 3,
) -> dict | list | None:
    """GET url with semaphore-based concurrency control and retry on 429/5xx."""
    async with semaphore:
        for attempt in range(max_retries):
            try:
                resp = await client.get(url)
                if resp.status_code == 429:
                    wait = 2 ** attempt * 5
                    log.warning("Rate limited by CR API, backing off %ds …", wait)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    wait = 2 ** attempt * 2
                    log.warning("Server error %d, retrying in %ds …", resp.status_code, wait)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                wait = 2 ** attempt * 3
                log.warning("Network error (%s), retrying in %ds …", exc, wait)
                await asyncio.sleep(wait)
    log.error("Giving up on %s after %d retries", url, max_retries)
    return None


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

async def fetch_leaderboard(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    season: str,
    top: int,
) -> list[dict]:
    """Return up to *top* leaderboard items from the Path of Legend endpoint.

    Each item contains at least: ``tag``, ``name``, ``rank``, ``leagueNumber``.

    If the requested season returns 0 items (season not started yet), falls
    back automatically to the previous calendar month.
    """
    for attempt_season in (season, _previous_season(season)):
        items: list[dict] = []
        after: str | None = None
        page_limit = min(top, 1000)

        while len(items) < top:
            params = f"?limit={page_limit}"
            if after:
                params += f"&after={after}"
            url = (
                CR_API_BASE
                + "/locations/global/pathoflegend/"
                + attempt_season
                + "/rankings/players"
                + params
            )

            data = await _fetch_with_retry(client, url, semaphore)
            if not data or not isinstance(data, dict):
                break

            page_items = data.get("items") or []
            for entry in page_items:
                items.append(entry)
                if len(items) >= top:
                    break

            paging = data.get("paging") or {}
            after = paging.get("cursors", {}).get("after")
            if not after or not page_items:
                break

        if items:
            log.info(
                "Path of Legend leaderboard [season %s]: %d entries (requested %d)",
                attempt_season, len(items), top,
            )
            return items

        log.warning(
            "Season %s returned 0 players — falling back to %s",
            attempt_season,
            _previous_season(attempt_season),
        )

    log.error("Could not fetch any players from the Path of Legend leaderboard.")
    return []


# ---------------------------------------------------------------------------
# Player profile
# ---------------------------------------------------------------------------

async def fetch_player_profile(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    tag: str,
) -> dict | None:
    """Fetch full player profile from ``GET /v1/players/{tag}``."""
    encoded = tag.replace("#", "%23")
    url = f"{CR_API_BASE}/players/{encoded}"
    return await _fetch_with_retry(client, url, semaphore)


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------

def _build_row(
    leaderboard_entry: dict,
    profile: dict,
    season: str,
    synced_at: datetime,
) -> dict:
    """Merge leaderboard item + full profile into a DB-ready dict."""
    tag = (profile.get("tag") or leaderboard_entry.get("tag") or "").lstrip("#").upper()
    return {
        "tag": tag,
        "name": profile.get("name") or leaderboard_entry.get("name"),
        "trophies": profile.get("trophies"),
        "best_trophies": profile.get("bestTrophies"),
        "exp_level": profile.get("expLevel"),
        "wins": profile.get("wins"),
        "losses": profile.get("losses"),
        "battle_count": profile.get("battleCount"),
        "league_number": leaderboard_entry.get("leagueNumber"),
        "league_rank": leaderboard_entry.get("rank"),
        "season": season,
        "current_deck": profile.get("currentDeck"),
        "raw_data": profile,
        "synced_at": synced_at,
    }


# ---------------------------------------------------------------------------
# Database upsert
# ---------------------------------------------------------------------------

async def upsert_players(session: AsyncSession, rows: list[dict]) -> int:
    """Insert or update player rows.  Returns number of rows affected."""
    if not rows:
        return 0

    stmt = (
        pg_insert(Player)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["tag"],
            set_={
                "name": pg_insert(Player).excluded.name,
                "trophies": pg_insert(Player).excluded.trophies,
                "best_trophies": pg_insert(Player).excluded.best_trophies,
                "exp_level": pg_insert(Player).excluded.exp_level,
                "wins": pg_insert(Player).excluded.wins,
                "losses": pg_insert(Player).excluded.losses,
                "battle_count": pg_insert(Player).excluded.battle_count,
                "league_number": pg_insert(Player).excluded.league_number,
                "league_rank": pg_insert(Player).excluded.league_rank,
                "season": pg_insert(Player).excluded.season,
                "current_deck": pg_insert(Player).excluded.current_deck,
                "raw_data": pg_insert(Player).excluded.raw_data,
                "synced_at": pg_insert(Player).excluded.synced_at,
            },
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount if result.rowcount != -1 else len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(top: int, season: str, concurrency: int, batch_size: int) -> None:
    settings = get_settings()

    if not settings.cr_api_token:
        log.error("CR_API_TOKEN is not set. Export it or add it to .env.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {settings.cr_api_token}",
        "Accept": "application/json",
    }

    log.info("Syncing Path of Legend players — season: %s, top: %d", season, top)

    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    semaphore = asyncio.Semaphore(concurrency)
    synced_at = datetime.now(tz=timezone.utc)

    total_upserted = 0
    total_errors = 0

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        # Step 1 — get leaderboard (ranks + basic info)
        leaderboard = await fetch_leaderboard(client, semaphore, season, top)
        if not leaderboard:
            log.error("No leaderboard data — aborting.")
            await engine.dispose()
            return

        log.info("Fetching full profiles for %d players …", len(leaderboard))

        # Step 2 — fetch full profiles in concurrent batches
        pending: list[dict] = []

        async def flush(force: bool = False) -> None:
            nonlocal total_upserted
            if not pending:
                return
            if not force and len(pending) < batch_size:
                return
            async with session_maker() as session:
                n = await upsert_players(session, list(pending))
            total_upserted += n
            log.info("DB flush: upserted %d  (total: %d)", n, total_upserted)
            pending.clear()

        for i in range(0, len(leaderboard), concurrency):
            chunk = leaderboard[i : i + concurrency]
            tasks = [
                fetch_player_profile(client, semaphore, entry["tag"])
                for entry in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for entry, result in zip(chunk, results):
                if isinstance(result, Exception):
                    log.warning("Error fetching profile for %s: %s", entry.get("tag"), result)
                    total_errors += 1
                    continue
                if result is None:
                    log.warning("Profile not found for %s (404)", entry.get("tag"))
                    total_errors += 1
                    continue

                row = _build_row(entry, result, season, synced_at)
                pending.append(row)
                await flush()

        await flush(force=True)

    await engine.dispose()

    log.info(
        "Done — %d players upserted, %d errors (season %s)",
        total_upserted, total_errors, season,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Path of Legend top players into the CRTracker database."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=1000,
        help="Number of top players to sync (default: 1000)",
    )
    parser.add_argument(
        "--season",
        type=str,
        default=_current_season(),
        help="Season in YYYY-MM format (default: current month)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Max concurrent CR API requests (default: 10)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        dest="batch_size",
        help="DB flush batch size (default: 100)",
    )
    args = parser.parse_args()

    asyncio.run(
        run(
            top=args.top,
            season=args.season,
            concurrency=args.concurrency,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
