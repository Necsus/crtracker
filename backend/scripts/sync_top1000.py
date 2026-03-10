"""Full top-1000 pipeline: leaderboard → player profiles → battle logs → decks.

This is the single recommended entry-point for a complete data refresh.
It replaces running sync_players, sync_battles, and extract_decks separately.

Usage
-----
From the backend/ directory (with venv activated)::

    # Full run – top 1000 players, current season
    python -m scripts.sync_top1000

    # Custom size
    python -m scripts.sync_top1000 --top 200

    # Specific season (format YYYY-MM, defaults to current month)
    python -m scripts.sync_top1000 --top 1000 --season 2026-02

    # Tune concurrency and noise filter
    python -m scripts.sync_top1000 --concurrency 8 --min-count 3

What it does (in order)
-----------------------
1.  **Leaderboard** – fetches the global Path of Legend ranking for the
    given season (auto-fallback to previous month if current has no data).
2.  **Profiles + battle logs** – for every player tag, concurrently fetches:
    - Full player profile (``GET /v1/players/{tag}``)
    - Recent battle log (``GET /v1/players/{tag}/battlelog``, ≤25 battles)
3.  **Player upsert** – bulk-upserts all profiles into ``players``
    (``ON CONFLICT (tag) DO UPDATE``).
4.  **Battle upsert** – bulk-upserts all new battles into ``battles``
    (``ON CONFLICT (battle_key) DO NOTHING``).
5.  **Deck aggregation** – from the battles collected in step 2, extracts
    unique decks played in **pathOfLegend** battles only, then upserts into
    ``decks``.  Existing decks are updated; new ones are inserted with an
    auto-generated name and archetype.

Rate limiting
-------------
The CR API allows ~100 requests/minute per IP.  A semaphore
(``--concurrency``, default 10) and exponential back-off on 429 responses
keep the script well within the limit.
"""

import argparse
import asyncio
import hashlib
import logging
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Bootstrap – make sure the app package is importable when running as a script
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]  # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.b_models.battle import Battle  # noqa: E402
from app.b_models.deck import Deck  # noqa: E402
from app.b_models.player import Player  # noqa: E402
from app.config import get_settings  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CR API helpers
# ---------------------------------------------------------------------------
CR_BASE = "https://api.clashroyale.com/v1"


def _current_season() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


def _previous_season() -> str:
    now = datetime.now(timezone.utc)
    first_day = now.replace(day=1)
    last_month = first_day - timedelta(days=1)
    return last_month.strftime("%Y-%m")


async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
    *,
    max_retries: int = 3,
) -> dict | list | None:
    """GET ``url`` with semaphore-based concurrency and exponential back-off."""
    async with semaphore:
        for attempt in range(max_retries):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    wait = 2**attempt * 5
                    log.warning("429 on %s – waiting %ss", url, wait)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    wait = 2**attempt * 2
                    log.warning("HTTP %s on %s – waiting %ss", resp.status_code, url, wait)
                    await asyncio.sleep(wait)
                    continue
                log.error("Unexpected HTTP %s for %s", resp.status_code, url)
                return None
            except httpx.NetworkError as exc:
                wait = 2**attempt * 3
                log.warning("Network error on %s: %s – retry in %ss", url, exc, wait)
                await asyncio.sleep(wait)
        log.error("Giving up on %s after %d attempts", url, max_retries)
        return None


# ---------------------------------------------------------------------------
# Phase 1 – Leaderboard
# ---------------------------------------------------------------------------

async def fetch_leaderboard(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    season: str,
    top: int,
) -> list[dict]:
    """Return up to *top* leaderboard entries for *season*."""
    url = (
        f"{CR_BASE}/locations/global/pathoflegend/{season}"
        f"/rankings/players?limit={top}"
    )
    data = await _fetch_with_retry(client, url, semaphore)
    entries = (data or {}).get("items", [])

    if not entries:
        fallback = _previous_season()
        log.info("No data for season %s – trying %s", season, fallback)
        url = (
            f"{CR_BASE}/locations/global/pathoflegend/{fallback}"
            f"/rankings/players?limit={top}"
        )
        data = await _fetch_with_retry(client, url, semaphore)
        entries = (data or {}).get("items", [])

    log.info("Leaderboard: %d entries", len(entries))
    return entries


# ---------------------------------------------------------------------------
# Phase 2 – Player profiles
# ---------------------------------------------------------------------------

def _build_player_row(entry: dict, profile: dict, season: str, synced_at: datetime) -> dict:
    """Merge a leaderboard entry with a full profile into a Player table row."""
    tag = profile.get("tag", entry.get("tag", ""))
    current_deck_raw = profile.get("currentDeck", [])
    current_deck = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "elixir": c.get("elixirCost"),
            "rarity": c.get("rarity"),
            "icon_url": c.get("iconUrls", {}).get("medium"),
        }
        for c in current_deck_raw
    ]
    return {
        "tag": tag,
        "name": profile.get("name", entry.get("name", "")),
        "trophies": profile.get("trophies", 0),
        "best_trophies": profile.get("bestTrophies", 0),
        "exp_level": profile.get("expLevel", 0),
        "wins": profile.get("wins", 0),
        "losses": profile.get("losses", 0),
        "battle_count": profile.get("battleCount", 0),
        "league_number": entry.get("leagueNumber"),
        "league_rank": entry.get("rank"),
        "season": season,
        "current_deck": current_deck,
        "raw_data": profile,
        "synced_at": synced_at,
    }


async def fetch_player_profile(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    tag: str,
) -> dict | None:
    encoded = tag.replace("#", "%23")
    return await _fetch_with_retry(client, f"{CR_BASE}/players/{encoded}", semaphore)


# ---------------------------------------------------------------------------
# Phase 3 – Battle logs
# ---------------------------------------------------------------------------

def _deck_key(card_ids: list[str]) -> str:
    return hashlib.sha1("|".join(sorted(card_ids)).encode()).hexdigest()


def _avg_elixir(cards: list[dict]) -> float:
    costs = [c.get("elixirCost", 0) for c in cards if c.get("elixirCost") is not None]
    if not costs:
        return 0.0
    return round(sum(costs) / len(costs), 2)


def _archetype(cards: list[dict], avg: float) -> str:
    max_elixir = max((c.get("elixirCost", 0) for c in cards), default=0)
    if avg < 2.9:
        return "Cycle"
    if max_elixir >= 7:
        return "Beatdown"
    if avg < 3.5:
        return "Midladder"
    return "Control"


def _deck_name(cards: list[dict]) -> str:
    sorted_cards = sorted(cards, key=lambda c: c.get("elixirCost", 0), reverse=True)
    top2 = sorted_cards[:2]
    return " + ".join(c.get("name", "Unknown") for c in top2)


def _to_deck_cards(raw_cards: list[dict]) -> list[dict]:
    return [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "elixir": c.get("elixirCost"),
            "rarity": c.get("rarity"),
            "type": None,
            "icon_url": c.get("iconUrls", {}).get("medium"),
        }
        for c in raw_cards
    ]


def _parse_battle(raw: dict) -> dict | None:
    """Normalise a raw battle entry into a Battle table row."""
    team = raw.get("team", [])
    opponent = raw.get("opponent", [])
    if not team or not opponent:
        return None

    t1 = team[0]
    t2 = opponent[0]
    t1_tag = t1.get("tag", "")
    t2_tag = t2.get("tag", "")

    # Sort teams deterministically so both players see the same row
    if t1_tag > t2_tag:
        t1, t2 = t2, t1
        t1_tag, t2_tag = t2_tag, t1_tag

    battle_time = raw.get("battleTime", "")
    key_src = f"{battle_time}|{t1_tag}|{t2_tag}"
    battle_key = hashlib.sha1(key_src.encode()).hexdigest()

    t1_crowns = t1.get("crowns", 0)
    t2_crowns = t2.get("crowns", 0)
    if t1_crowns > t2_crowns:
        winner_tag = t1_tag
    elif t2_crowns > t1_crowns:
        winner_tag = t2_tag
    else:
        winner_tag = None

    game_mode = raw.get("gameMode", {})

    return {
        "battle_key": battle_key,
        "battle_time": battle_time,
        "battle_type": raw.get("type", ""),
        "game_mode_id": game_mode.get("id"),
        "game_mode_name": game_mode.get("name"),
        "arena_id": raw.get("arena", {}).get("id"),
        "arena_name": raw.get("arena", {}).get("name"),
        "team1_tag": t1_tag,
        "team1_name": t1.get("name", ""),
        "team1_crowns": t1_crowns,
        "team1_starting_trophies": t1.get("startingTrophies"),
        "team1_trophy_change": t1.get("trophyChange"),
        "team1_cards": _to_deck_cards(t1.get("cards", [])),
        "team2_tag": t2_tag,
        "team2_name": t2.get("name", ""),
        "team2_crowns": t2_crowns,
        "team2_starting_trophies": t2.get("startingTrophies"),
        "team2_trophy_change": t2.get("trophyChange"),
        "team2_cards": _to_deck_cards(t2.get("cards", [])),
        "winner_tag": winner_tag,
        "raw_data": raw,
    }


async def fetch_battle_log(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    tag: str,
) -> list[dict]:
    encoded = tag.replace("#", "%23")
    data = await _fetch_with_retry(client, f"{CR_BASE}/players/{encoded}/battlelog", semaphore)
    return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# Phase 2+3 combined – fetch one player's profile AND battle log
# ---------------------------------------------------------------------------

async def _fetch_player_data(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    entry: dict,
    season: str,
    synced_at: datetime,
) -> tuple[dict | None, list[dict]]:
    """Concurrently fetch profile + battlelog for one leaderboard entry."""
    tag = entry.get("tag", "")
    profile_task = asyncio.create_task(fetch_player_profile(client, semaphore, tag))
    battles_task = asyncio.create_task(fetch_battle_log(client, semaphore, tag))
    profile, raw_battles = await asyncio.gather(profile_task, battles_task)

    player_row = None
    if profile:
        player_row = _build_player_row(entry, profile, season, synced_at)

    parsed_battles = []
    for raw in raw_battles:
        parsed = _parse_battle(raw)
        if parsed:
            parsed_battles.append(parsed)

    return player_row, parsed_battles


# ---------------------------------------------------------------------------
# DB upserts
# ---------------------------------------------------------------------------

async def upsert_players(session: AsyncSession, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = pg_insert(Player).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["tag"],
        set_={
            "name": stmt.excluded.name,
            "trophies": stmt.excluded.trophies,
            "best_trophies": stmt.excluded.best_trophies,
            "exp_level": stmt.excluded.exp_level,
            "wins": stmt.excluded.wins,
            "losses": stmt.excluded.losses,
            "battle_count": stmt.excluded.battle_count,
            "league_number": stmt.excluded.league_number,
            "league_rank": stmt.excluded.league_rank,
            "season": stmt.excluded.season,
            "current_deck": stmt.excluded.current_deck,
            "raw_data": stmt.excluded.raw_data,
            "synced_at": stmt.excluded.synced_at,
        },
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)


async def upsert_battles(
    session: AsyncSession, rows: list[dict]
) -> tuple[int, int]:
    if not rows:
        return 0, 0
    stmt = pg_insert(Battle).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["battle_key"])
    result = await session.execute(stmt)
    await session.commit()
    inserted = result.rowcount if result.rowcount and result.rowcount >= 0 else 0
    skipped = len(rows) - inserted
    return inserted, skipped


async def upsert_decks(
    session: AsyncSession,
    battle_rows: list[dict],
    min_count: int,
) -> tuple[int, int]:
    """Aggregate decks from *battle_rows* (pathOfLegend only) and upsert."""
    # ---- aggregate --------------------------------------------------------
    plays: dict[str, int] = defaultdict(int)
    wins: dict[str, int] = defaultdict(int)
    deck_cards_map: dict[str, list[dict]] = {}  # deck_key → raw card list

    for battle in battle_rows:
        if battle.get("battle_type") != "pathOfLegend":
            continue

        for side in ("team1_cards", "team2_cards"):
            cards = battle.get(side, [])
            if not cards:
                continue
            card_ids = [str(c.get("id", "")) for c in cards if c.get("id") is not None]
            if len(card_ids) != 8:
                continue
            dk = _deck_key(card_ids)
            plays[dk] += 1
            deck_cards_map[dk] = cards

            # Determine if this side won
            side_tag_key = "team1_tag" if side == "team1_cards" else "team2_tag"
            if battle.get("winner_tag") == battle.get(side_tag_key):
                wins[dk] += 1

    # ---- filter noise -----------------------------------------------------
    qualified = {dk for dk, p in plays.items() if p >= min_count}
    log.info("Decks after min-count filter (%d): %d", min_count, len(qualified))

    if not qualified:
        return 0, 0

    # ---- load existing deck_keys from DB ----------------------------------
    rows_existing = await session.execute(
        text("SELECT id, matchup_stats->>'deck_key' AS dk FROM decks")
    )
    existing: dict[str, int] = {
        row.dk: row.id for row in rows_existing if row.dk
    }

    inserted = 0
    updated = 0

    for dk in qualified:
        raw_cards = deck_cards_map[dk]
        p = plays[dk]
        w = wins[dk]
        winrate = round(w / p * 100, 2) if p else 0.0

        matchup_stats = {
            "deck_key": dk,
            "global_winrate": winrate,
            "meta_share": 0.0,
            "sample_size": p,
            "wins": w,
            "matchups": {},
        }

        if dk in existing:
            await session.execute(
                text(
                    "UPDATE decks SET matchup_stats = :ms, avg_elixir = :avg,"
                    " updated_at = NOW() WHERE id = :id"
                ),
                {
                    "ms": matchup_stats,
                    "avg": _avg_elixir(raw_cards),
                    "id": existing[dk],
                },
            )
            updated += 1
        else:
            avg = _avg_elixir(raw_cards)
            deck = Deck(
                name=_deck_name(raw_cards),
                archetype=_archetype(raw_cards, avg),
                cards=raw_cards,
                avg_elixir=avg,
                player_tag=None,
                matchup_stats=matchup_stats,
                oracle_cache={},
            )
            session.add(deck)
            inserted += 1

    await session.commit()
    return inserted, updated


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run(
    *,
    top: int,
    season: str,
    concurrency: int,
    min_count: int,
    batch_size: int,
) -> None:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.cr_api_token}"}

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    semaphore = asyncio.Semaphore(concurrency)
    synced_at = datetime.now(timezone.utc)

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        # ---- Phase 1: leaderboard ----------------------------------------
        log.info("=== Phase 1: fetching leaderboard (top %d, season %s) ===", top, season)
        entries = await fetch_leaderboard(client, semaphore, season, top)
        if not entries:
            log.error("No leaderboard entries found – aborting.")
            await engine.dispose()
            return

        # ---- Phase 2+3: profiles + battle logs ---------------------------
        log.info("=== Phase 2+3: fetching profiles and battle logs for %d players ===", len(entries))

        player_rows: list[dict] = []
        all_battle_rows: list[dict] = []
        seen_battle_keys: set[str] = set()

        tasks = [
            _fetch_player_data(client, semaphore, entry, season, synced_at)
            for entry in entries
        ]

        done = 0
        for coro in asyncio.as_completed(tasks):
            player_row, battle_rows = await coro
            done += 1
            if done % 100 == 0 or done == len(entries):
                log.info("  ... %d / %d players processed", done, len(entries))

            if player_row:
                player_rows.append(player_row)

            for br in battle_rows:
                bk = br["battle_key"]
                if bk not in seen_battle_keys:
                    seen_battle_keys.add(bk)
                    all_battle_rows.append(br)

        log.info(
            "Collected %d player profiles, %d unique battles",
            len(player_rows),
            len(all_battle_rows),
        )

        # ---- Phase 3: DB writes ------------------------------------------
        async with session_factory() as session:
            log.info("=== Phase 3: upserting players ===")
            upserted_players = await upsert_players(session, player_rows)
            log.info("Players upserted: %d", upserted_players)

            log.info("=== Phase 4: upserting battles ===")
            battle_inserted = 0
            battle_skipped = 0
            for i in range(0, len(all_battle_rows), batch_size):
                chunk = all_battle_rows[i : i + batch_size]
                ins, skp = await upsert_battles(session, chunk)
                battle_inserted += ins
                battle_skipped += skp
            log.info("Battles – inserted: %d, already present: %d", battle_inserted, battle_skipped)

            log.info("=== Phase 5: aggregating and upserting decks (pathOfLegend only) ===")
            deck_inserted, deck_updated = await upsert_decks(session, all_battle_rows, min_count)
            log.info("Decks – inserted: %d, updated: %d", deck_inserted, deck_updated)

    await engine.dispose()

    log.info(
        "\n=== Done === players: %d | battles in: %d skip: %d | decks new: %d upd: %d",
        upserted_players,
        battle_inserted,
        battle_skipped,
        deck_inserted,
        deck_updated,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Full top-1000 PoL sync: leaderboard → profiles → battles → decks."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=1000,
        help="Number of top players to sync (default: 1000)",
    )
    parser.add_argument(
        "--season",
        default=_current_season(),
        help="Season in YYYY-MM format (default: current month)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Max concurrent API requests (default: 10)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        dest="min_count",
        help="Minimum times a deck must appear to be stored (default: 2)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        dest="batch_size",
        help="DB batch size for battle upserts (default: 100)",
    )
    args = parser.parse_args()

    asyncio.run(
        run(
            top=args.top,
            season=args.season,
            concurrency=args.concurrency,
            min_count=args.min_count,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
