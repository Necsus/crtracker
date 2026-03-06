"""Extract and aggregate unique decks from battle logs, then upsert into the decks table.

Usage
-----
From the backend/ directory (with venv activated)::

    # Extract all decks from all battles
    python -m scripts.extract_decks

    # Only process pathOfLegend battles
    python -m scripts.extract_decks --battle-type pathOfLegend

    # Minimum appearances before a deck is stored (noise filter)
    python -m scripts.extract_decks --min-count 3

What it does
------------
1.  Reads every row in the ``battles`` table (streamed by batch to avoid
    loading all rows into memory at once).
2.  For each battle, extracts the 8 cards in team1 and team2.
3.  Deduplicates decks by a canonical key = sha1(sorted card IDs).
    The same 8 cards in any order map to the same key.
4.  Aggregates for each unique deck:
    - ``plays``   : total number of times that deck was played
    - ``wins``    : number of times that deck won
    - ``global_winrate`` : wins / plays * 100
5.  Filters out decks with fewer than ``--min-count`` plays.
6.  Upserts into the ``decks`` table:
    - New decks are inserted with an auto-generated name.
    - Existing decks (matched by ``deck_key`` stored in
      ``matchup_stats['deck_key']``) have their stats updated.
7.  Prints a summary: X inserted, Y updated.

Auto-naming
-----------
Deck names are derived from the two highest-elixir cards.
Archetype is guessed heuristically:
  avg_elixir < 2.9  → "Cycle"
  avg_elixir < 3.5  → "Midladder"
  highest elixir ≥ 7 → "Beatdown"
  otherwise          → "Control"
"""

import argparse
import asyncio
import hashlib
import logging
import pathlib
import sys
from collections import defaultdict

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.b_models.battle import Battle  # noqa: E402
from app.b_models.deck import Deck  # noqa: E402
from app.config import get_settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deck_key(card_ids: list[int]) -> str:
    """Canonical dedup key for a set of 8 cards (order-independent)."""
    return hashlib.sha1("|".join(str(i) for i in sorted(card_ids)).encode()).hexdigest()


def _avg_elixir(cards: list[dict]) -> float:
    costs = [c.get("elixirCost") or 0 for c in cards]
    return round(sum(costs) / len(costs), 2) if costs else 0.0


def _archetype(cards: list[dict], avg: float) -> str:
    max_elixir = max((c.get("elixirCost") or 0 for c in cards), default=0)
    if avg < 2.9:
        return "Cycle"
    if max_elixir >= 7:
        return "Beatdown"
    if avg < 3.5:
        return "Midladder"
    return "Control"


def _deck_name(cards: list[dict]) -> str:
    """Generate a human-readable deck name from the two highest-elixir cards."""
    sorted_cards = sorted(cards, key=lambda c: c.get("elixirCost") or 0, reverse=True)
    names = [c.get("name", "?") for c in sorted_cards[:2]]
    return " + ".join(names)


def _to_deck_cards(raw_cards: list[dict]) -> list[dict]:
    """Convert CR API card format → deck card format used by the decks table."""
    result = []
    for c in raw_cards:
        icon_urls = c.get("iconUrls") or {}
        result.append({
            "id": str(c.get("id", "")),
            "name": c.get("name", ""),
            "elixir": c.get("elixirCost") or 0,
            "rarity": (c.get("rarity") or "common").lower(),
            "type": None,
            "icon_url": icon_urls.get("medium"),
        })
    return result


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

async def aggregate_decks(
    session: AsyncSession,
    battle_type: str | None,
    batch_size: int,
) -> dict[str, dict]:
    """
    Stream all battles and aggregate deck stats.

    Returns:
        Dict keyed by deck_key → {
            "cards": list[dict],        # raw CR API card objects
            "plays": int,
            "wins": int,
        }
    """
    stats: dict[str, dict] = {}

    offset = 0
    total_processed = 0

    while True:
        stmt = select(
            Battle.team1_tag,
            Battle.team1_cards,
            Battle.team2_tag,
            Battle.team2_cards,
            Battle.winner_tag,
        ).order_by(Battle.id)

        if battle_type:
            stmt = stmt.where(Battle.battle_type == battle_type)

        stmt = stmt.offset(offset).limit(batch_size)
        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            break

        for t1_tag, t1_cards, t2_tag, t2_cards, winner_tag in rows:
            for cards, tag in ((t1_cards, t1_tag), (t2_cards, t2_tag)):
                if not cards or len(cards) < 8:
                    continue
                card_ids = [c.get("id") for c in cards if c.get("id")]
                if len(card_ids) < 8:
                    continue
                key = _deck_key(card_ids)
                if key not in stats:
                    stats[key] = {"cards": cards, "plays": 0, "wins": 0}
                stats[key]["plays"] += 1
                if winner_tag == tag:
                    stats[key]["wins"] += 1

        total_processed += len(rows)
        log.info("Processed %d battles so far …", total_processed)
        offset += batch_size

    log.info("Aggregation complete. %d unique decks found in %d battles.", len(stats), total_processed)
    return stats


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

async def upsert_decks(
    session: AsyncSession,
    stats: dict[str, dict],
    min_count: int,
) -> tuple[int, int]:
    """Upsert aggregated decks into the decks table.

    Decks are matched by ``matchup_stats->>'deck_key'``.
    Returns (inserted, updated).
    """
    # Load existing deck_keys from DB
    result = await session.execute(
        text("SELECT id, matchup_stats->>'deck_key' AS dk FROM decks WHERE matchup_stats->>'deck_key' IS NOT NULL")
    )
    existing: dict[str, int] = {row.dk: row.id for row in result}

    inserted = 0
    updated = 0

    for deck_key, agg in stats.items():
        if agg["plays"] < min_count:
            continue

        cards = agg["cards"]
        avg = _avg_elixir(cards)
        archetype = _archetype(cards, avg)
        name = _deck_name(cards)
        winrate = round(agg["wins"] / agg["plays"] * 100, 2) if agg["plays"] > 0 else 0.0

        matchup_stats = {
            "deck_key": deck_key,
            "global_winrate": winrate,
            "meta_share": 0.0,
            "sample_size": agg["plays"],
            "wins": agg["wins"],
            "matchups": {},
        }

        deck_cards_json = _to_deck_cards(cards)

        if deck_key in existing:
            # Update existing deck stats
            await session.execute(
                text("""
                    UPDATE decks
                    SET matchup_stats = :ms,
                        avg_elixir   = :avg,
                        updated_at   = NOW()
                    WHERE id = :id
                """),
                {"ms": matchup_stats, "avg": avg, "id": existing[deck_key]},
            )
            updated += 1
        else:
            # Insert new deck
            deck = Deck(
                name=name,
                archetype=archetype,
                cards=deck_cards_json,
                avg_elixir=avg,
                player_tag=None,
                matchup_stats=matchup_stats,
                oracle_cache={},
            )
            session.add(deck)
            inserted += 1

        # Flush periodically to avoid huge transactions
        if (inserted + updated) % 200 == 0:
            await session.flush()

    await session.commit()
    return inserted, updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(battle_type: str | None, min_count: int, batch_size: int) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        log.info(
            "Aggregating decks from battles (type=%s, min_count=%d) …",
            battle_type or "all",
            min_count,
        )
        stats = await aggregate_decks(session, battle_type, batch_size)

        log.info("Upserting decks …")
        inserted, updated = await upsert_decks(session, stats, min_count)

    await engine.dispose()

    total_eligible = sum(1 for v in stats.values() if v["plays"] >= min_count)
    log.info(
        "─── Extract complete ───  unique decks=%d  eligible (≥%d plays)=%d  "
        "inserted=%d  updated=%d",
        len(stats),
        min_count,
        total_eligible,
        inserted,
        updated,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract unique decks from battle logs into the decks table.")
    parser.add_argument(
        "--battle-type",
        default=None,
        metavar="TYPE",
        help="Only process battles of this type (e.g. pathOfLegend). Default: all types.",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        metavar="N",
        help="Minimum number of plays before a deck is stored (default: 2)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        metavar="B",
        help="Number of battles to read per DB query (default: 1000)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(run(args.battle_type, args.min_count, args.batch_size))
