"""Sync Clash Royale battle data into the local database.

Usage
-----
From the backend/ directory (with venv activated)::

    # Fetch battles for the global top 1000 Path of Legend players (current season)
    python -m scripts.sync_battles

    # Custom top size
    python -m scripts.sync_battles --top 200

    # Specific season (format YYYY-MM, defaults to current month)
    python -m scripts.sync_battles --top 1000 --season 2026-02

    # Recursive expansion: also fetch battles of all opponents found in
    # the initial top-N players' logs (depth=1), then their opponents (depth=2)…
    python -m scripts.sync_battles --top 200 --depth 1

What it does
------------
1.  Fetches ``GET /v1/locations/global/pathoflegend/{season}/rankings/players?limit=N``
    (Path of Legend global leaderboard) to get the top-N player tags.
    Season defaults to the current calendar month (YYYY-MM). If the
    current month has no data yet, it automatically falls back to the
    previous month.
2.  For each player tag in the queue, fetches
    ``GET /v1/players/{tag}/battlelog`` (returns up to 25 recent matches).
3.  Parses every battle into a normalised form:
    - The two players are sorted alphabetically by tag so the same game
      seen from both players' logs always produces the same ``battle_key``
      → **no duplicate rows ever inserted**.
4.  If ``--depth > 0``, opponent tags discovered in this round are added
    to the queue and their battle logs are fetched in the next round
    (BFS expansion, each tag is processed at most once).
5.  Upserts every new battle with ``ON CONFLICT DO NOTHING`` – safe to
    re-run as many times as you like.
6.  Prints a final summary: X inserted, Y already present, Z errors.

Rate limiting
-------------
The CR API allows ~100 requests/minute per IP.  The script uses an
asyncio semaphore (``--concurrency``, default 10) to stay comfortably
under the limit.  A short back-off is applied on 429 responses.
"""

import argparse
import asyncio
import hashlib
import logging
import pathlib
import sys
from collections import deque
from datetime import datetime, timezone, timedelta
from calendar import monthrange

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Bootstrap – make sure the app package is importable when running as a script
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(ROOT))

from app.b_models.battle import Battle  # noqa: E402
from app.b_models.card import Card  # noqa: E402, F401
from app.b_models.deck import Deck  # noqa: E402, F401
from app.b_models.player import Player  # noqa: E402, F401
from app.b_models.player_season_rank import PlayerSeasonRank  # noqa: E402, F401
from app.b_models.season import Season  # noqa: E402, F401
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

def _parse_battle_time(raw: str) -> datetime:
    """Parse the CR API battleTime format '20250306T123456.000Z'."""
    # The format used by the CR API:  YYYYMMDDTHHmmss.sssZ
    try:
        return datetime.strptime(raw, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)
    except ValueError:
        # Fallback: ISO-8601 in case the format ever changes
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _make_battle_key(battle_time: str, tag1: str, tag2: str) -> str:
    """
    Normalised dedup key that is the same regardless of which player's
    battle log the game was fetched from.

    Format: sha1("{battleTime}|{lower_tag}|{upper_tag}")
    Using a hash keeps the key a fixed length and avoids any special
    character concerns with player tags.
    """
    tags = sorted([tag1.lstrip("#"), tag2.lstrip("#")])
    raw = f"{battle_time}|{tags[0]}|{tags[1]}"
    return hashlib.sha1(raw.encode()).hexdigest()


def _parse_battle(raw: dict) -> dict | None:
    """
    Convert a raw CR API battle object into a DB-ready dict.

    Returns None if the battle cannot be parsed (e.g. not a 1v1 match).
    """
    try:
        team = raw.get("team") or []
        opponent = raw.get("opponent") or []

        # Only handle 1v1 battles (regular ladder, tournaments, …)
        if len(team) != 1 or len(opponent) != 1:
            return None

        p1 = team[0]
        p2 = opponent[0]

        tag1_raw: str = p1.get("tag", "")
        tag2_raw: str = p2.get("tag", "")
        if not tag1_raw or not tag2_raw:
            return None

        battle_time_str: str = raw.get("battleTime", "")
        if not battle_time_str:
            return None

        battle_time = _parse_battle_time(battle_time_str)
        battle_key = _make_battle_key(battle_time_str, tag1_raw, tag2_raw)

        # Normalise: sort by tag so the canonical "team1" is always the
        # alphabetically lower tag.  This makes the row identical no matter
        # from which player's log it was fetched.
        if tag1_raw.lstrip("#") <= tag2_raw.lstrip("#"):
            a, b = p1, p2
        else:
            a, b = p2, p1

        crowns_a = a.get("crowns", 0) or 0
        crowns_b = b.get("crowns", 0) or 0

        if crowns_a > crowns_b:
            winner_tag = a.get("tag")
        elif crowns_b > crowns_a:
            winner_tag = b.get("tag")
        else:
            winner_tag = None  # draw

        arena = raw.get("arena") or {}
        game_mode = raw.get("gameMode") or {}

        return {
            "battle_key": battle_key,
            "battle_time": battle_time,
            "battle_type": raw.get("type"),
            "game_mode_id": game_mode.get("id"),
            "game_mode_name": game_mode.get("name"),
            "arena_id": arena.get("id"),
            "arena_name": arena.get("name"),
            "team1_tag": a.get("tag", ""),
            "team1_name": a.get("name"),
            "team1_crowns": crowns_a,
            "team1_starting_trophies": a.get("startingTrophies"),
            "team1_trophy_change": a.get("trophyChange"),
            "team1_cards": a.get("cards"),
            "team2_tag": b.get("tag", ""),
            "team2_name": b.get("name"),
            "team2_crowns": crowns_b,
            "team2_starting_trophies": b.get("startingTrophies"),
            "team2_trophy_change": b.get("trophyChange"),
            "team2_cards": b.get("cards"),
            "winner_tag": winner_tag,
            "raw_data": raw,
        }
    except Exception as exc:
        log.debug("Failed to parse battle: %s — %s", exc, raw.get("battleTime"))
        return None


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
                    wait = 2 ** attempt * 5  # 5s, 10s, 20s
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

def _current_season() -> str:
    """Return the current season in YYYY-MM format (today's month)."""
    now = datetime.now(tz=timezone.utc)
    return now.strftime("%Y-%m")


def _previous_season(season: str) -> str:
    """Return the season one month before the given YYYY-MM season."""
    year, month = int(season[:4]), int(season[5:7])
    first_of_month = datetime(year, month, 1)
    prev = first_of_month - timedelta(days=1)
    return prev.strftime("%Y-%m")


async def fetch_leaderboard(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    season: str,
    top: int,
) -> list[str]:
    """Return up to *top* player tags from the Path of Legend global leaderboard.

    Uses ``GET /v1/locations/global/pathoflegend/{season}/rankings/players``.
    If the requested season has no data yet (returns 0 items), automatically
    falls back to the previous calendar month.

    Args:
        season: Season in YYYY-MM format, e.g. "2026-02".
        top:    Maximum number of player tags to return.
    """
    for attempt_season in (season, _previous_season(season)):
        tags: list[str] = []
        after: str | None = None
        page_limit = min(top, 1000)

        while len(tags) < top:
            params = "?limit=" + str(page_limit)
            if after:
                params += "&after=" + after
            url = CR_API_BASE + "/locations/global/pathoflegend/" + attempt_season + "/rankings/players" + params

            data = await _fetch_with_retry(client, url, semaphore)
            if not data or not isinstance(data, dict):
                break

            items = data.get("items") or []
            for item in items:
                tag = item.get("tag")
                if tag:
                    tags.append(tag)
                if len(tags) >= top:
                    break

            paging = data.get("paging") or {}
            after = paging.get("cursors", {}).get("after")
            if not after or not items:
                break

        if tags:
            log.info(
                "Path of Legend leaderboard [season %s]: fetched %d player tags (requested %d)",
                attempt_season, len(tags), top,
            )
            return tags

        log.warning(
            "Season %s returned 0 players — falling back to season %s",
            attempt_season, _previous_season(attempt_season),
        )

    log.error("Could not fetch any players from Path of Legend leaderboard.")
    return []


# ---------------------------------------------------------------------------
# Battle log for one player
# ---------------------------------------------------------------------------

async def fetch_battle_log(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    player_tag: str,
) -> list[dict]:
    """Return raw battle objects from a player's battle log."""
    encoded_tag = player_tag.replace("#", "%23")
    url = f"{CR_API_BASE}/players/{encoded_tag}/battlelog"
    data = await _fetch_with_retry(client, url, semaphore)
    if data is None:
        return []
    if not isinstance(data, list):
        return []
    return data


# ---------------------------------------------------------------------------
# Database upsert
# ---------------------------------------------------------------------------

async def upsert_battles(
    session: AsyncSession,
    rows: list[dict],
) -> tuple[int, int]:
    """
    Insert battles that don't already exist, skip duplicates.

    Returns:
        (inserted, skipped) counts
    """
    if not rows:
        return 0, 0

    stmt = (
        pg_insert(Battle)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["battle_key"])
    )
    result = await session.execute(stmt)
    await session.commit()

    inserted = result.rowcount if result.rowcount != -1 else len(rows)
    skipped = len(rows) - inserted
    return inserted, skipped


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def run(
    top: int,
    depth: int,
    season: str,
    concurrency: int,
    batch_size: int,
) -> None:
    settings = get_settings()

    if not settings.cr_api_token:
        log.error("CR_API_TOKEN is not set. Export it or add it to .env.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {settings.cr_api_token}",
        "Accept": "application/json",
    }

    log.info("Targeting Path of Legend season: %s", season)

    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Ensure table exists (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    semaphore = asyncio.Semaphore(concurrency)

    total_inserted = 0
    total_skipped = 0
    total_errors = 0

    # --- BFS queue of player tags to process ---
    # visited: set of tags already fetched (so recursive expansion never
    #          re-fetches the same player)
    visited: set[str] = set()
    # queue of (tag, current_depth) tuples
    queue: deque[tuple[str, int]] = deque()

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:

        # Seed the queue with the Path of Legend leaderboard
        leaderboard_tags = await fetch_leaderboard(client, semaphore, season, top)
        for tag in leaderboard_tags:
            queue.append((tag, 0))
            visited.add(tag)

        log.info(
            "Starting battle sync: %d players, depth=%d, concurrency=%d",
            len(queue),
            depth,
            concurrency,
        )

        pending_rows: list[dict] = []

        # Helper: flush pending rows to DB
        async def flush(force: bool = False) -> None:
            nonlocal total_inserted, total_skipped
            if not pending_rows:
                return
            if not force and len(pending_rows) < batch_size:
                return
            async with session_maker() as session:
                ins, skp = await upsert_battles(session, list(pending_rows))
            total_inserted += ins
            total_skipped += skp
            log.info(
                "DB flush: +%d inserted, %d skipped  (total: %d inserted, %d skipped)",
                ins, skp, total_inserted, total_skipped,
            )
            pending_rows.clear()

        # Process queue level by level (BFS) so we can honour --depth
        while queue:
            # Pull up to `concurrency` tags from the queue for this batch
            batch: list[tuple[str, int]] = []
            while queue and len(batch) < concurrency:
                batch.append(queue.popleft())

            # Fetch battle logs concurrently for this batch
            tasks = [
                fetch_battle_log(client, semaphore, tag)
                for tag, _ in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (tag, current_depth), result in zip(batch, results):
                if isinstance(result, Exception):
                    log.warning("Error fetching battles for %s: %s", tag, result)
                    total_errors += 1
                    continue

                raw_battles: list[dict] = result  # type: ignore[assignment]

                for raw in raw_battles:
                    parsed = _parse_battle(raw)
                    if parsed is None:
                        continue
                    pending_rows.append(parsed)

                    # Recursive expansion: if within depth limit, enqueue
                    # opponents we haven't seen yet
                    if current_depth < depth:
                        for opp_tag in (parsed["team1_tag"], parsed["team2_tag"]):
                            if opp_tag and opp_tag not in visited:
                                visited.add(opp_tag)
                                queue.append((opp_tag, current_depth + 1))

                await flush()

        # Final flush of any remaining rows
        await flush(force=True)

    await engine.dispose()

    log.info(
        "─── Sync complete ───  inserted=%d  skipped=%d  errors=%d  "
        "unique players processed=%d",
        total_inserted,
        total_skipped,
        total_errors,
        len(visited),
    )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync CR battle data for the top-N global players.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=1000,
        metavar="N",
        help="Number of players to pull from the global leaderboard (default: 1000)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=0,
        metavar="D",
        help=(
            "Recursive expansion depth.  0 = only top-N players, "
            "1 = also fetch their opponents, 2 = fetch opponents' opponents, …  "
            "(default: 0)"
        ),
    )
    parser.add_argument(
        "--season",
        default=None,
        metavar="YYYY-MM",
        help=(
            "Path of Legend season to seed from, e.g. 2026-02.  "
            "Defaults to the current calendar month and falls back to the "
            "previous month if the current month has no data yet."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        metavar="C",
        help="Max simultaneous HTTP requests (default: 10)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        metavar="B",
        help="Number of battles to accumulate before a DB flush (default: 500)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(
        run(
            top=args.top,
            depth=args.depth,
            season=args.season or _current_season(),
            concurrency=args.concurrency,
            batch_size=args.batch_size,
        )
    )
