"""Compute deck win/loss statistics from battle data and update matchup_stats.

Usage
-----
From the backend/ directory (with venv activated)::

    python -m scripts.compute_deck_stats

What it does
------------
1.  Loads every deck from the DB and builds a ``frozenset(card_names) → deck_id``
    lookup (identifies a deck by its 8 card names — same strategy used by the
    battle filter query).
2.  Pages through every battle row in the ``battles`` table.
3.  For each battle:
    - Extracts team1 / team2 card name sets.
    - Resolves each set to a known deck_id (if any).
    - Determines the outcome (win / loss; draws are skipped).
    - Accumulates global and per-matchup wins/losses for each identified deck.
4.  Computes derived metrics:
    - ``global_winrate``: wins / (wins + losses) × 100
    - ``meta_share``:     deck appearances / total appearances across all decks × 100
5.  Writes the updated ``matchup_stats`` JSONB back to each deck row (preserving
    any existing keys such as ``oracle_cache`` that may live alongside).

Run this script after every ``sync_battles`` run to keep stats fresh.
"""

from __future__ import annotations

import asyncio
import logging
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Bootstrap imports
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(ROOT))

from app.b_models.battle import Battle  # noqa: E402
from app.b_models.deck import Deck  # noqa: E402
from app.c_bll.deck_service import DeckService  # noqa: E402
from app.config import get_settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BATTLE_CHUNK = 500  # battles to load per page


def _card_names(cards: list | None) -> frozenset[str]:
    """Extract the set of card names from a raw battle cards list."""
    if not isinstance(cards, list):
        return frozenset()
    return frozenset(
        c["name"] for c in cards if isinstance(c, dict) and c.get("name")
    )


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

async def compute_stats(session: AsyncSession) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # 1. Load all decks and build card-name-set ↔ deck_id lookups
    # ------------------------------------------------------------------
    log.info("Loading decks…")
    result = await session.execute(select(Deck))
    decks: list[Deck] = list(result.scalars().all())
    log.info("Loaded %d decks.", len(decks))

    card_set_to_deck: dict[frozenset[str], int] = {}
    deck_ids_with_8: set[int] = set()

    for deck in decks:
        cards = DeckService._extract_cards(deck.cards)
        names = frozenset(c["name"] for c in cards)
        if len(names) == 8:
            # Last writer wins when two decks share the exact same 8 cards
            card_set_to_deck[names] = deck.id
            deck_ids_with_8.add(deck.id)

    log.info("Matched %d decks with exactly 8 unique card names.", len(deck_ids_with_8))

    # ------------------------------------------------------------------
    # 2. Initialise accumulators
    # ------------------------------------------------------------------
    # {deck_id: {"wins": int, "losses": int}}
    global_acc: dict[int, dict[str, int]] = {
        d: {"wins": 0, "losses": 0} for d in deck_ids_with_8
    }
    # {deck_id: {opp_deck_id: {"wins": int, "losses": int}}}
    matchup_acc: dict[int, dict[int, dict[str, int]]] = {
        d: defaultdict(lambda: {"wins": 0, "losses": 0}) for d in deck_ids_with_8
    }

    # ------------------------------------------------------------------
    # 3. Page through all battles
    # ------------------------------------------------------------------
    offset = 0
    total_processed = 0

    while True:
        result = await session.execute(
            select(Battle).order_by(Battle.id).offset(offset).limit(BATTLE_CHUNK)
        )
        battles: list[Battle] = list(result.scalars().all())
        if not battles:
            break

        for battle in battles:
            t1_names = _card_names(battle.team1_cards)
            t2_names = _card_names(battle.team2_cards)

            t1_deck = card_set_to_deck.get(t1_names)
            t2_deck = card_set_to_deck.get(t2_names)

            # Skip if neither team uses a tracked deck
            if t1_deck is None and t2_deck is None:
                continue

            # Determine outcome — skip draws
            if battle.winner_tag is None:
                continue
            if battle.winner_tag == battle.team1_tag:
                t1_won = True
            elif battle.winner_tag == battle.team2_tag:
                t1_won = False
            else:
                continue  # data integrity issue — skip

            # ---- accumulate for deck used by team1 ----
            if t1_deck is not None:
                if t1_won:
                    global_acc[t1_deck]["wins"] += 1
                else:
                    global_acc[t1_deck]["losses"] += 1

                if t2_deck is not None and t2_deck != t1_deck:
                    mu = matchup_acc[t1_deck][t2_deck]
                    if t1_won:
                        mu["wins"] += 1
                    else:
                        mu["losses"] += 1

            # ---- accumulate for deck used by team2 ----
            if t2_deck is not None:
                t2_won = not t1_won
                if t2_won:
                    global_acc[t2_deck]["wins"] += 1
                else:
                    global_acc[t2_deck]["losses"] += 1

                if t1_deck is not None and t1_deck != t2_deck:
                    mu = matchup_acc[t2_deck][t1_deck]
                    if t2_won:
                        mu["wins"] += 1
                    else:
                        mu["losses"] += 1

        total_processed += len(battles)
        offset += BATTLE_CHUNK
        log.info("  … processed %d battles", total_processed)

    log.info("Total battles processed: %d", total_processed)

    # ------------------------------------------------------------------
    # 4. Compute meta_share denominator
    #    = total deck appearances across all tracked decks
    # ------------------------------------------------------------------
    total_appearances = sum(
        g["wins"] + g["losses"] for g in global_acc.values()
    )

    # ------------------------------------------------------------------
    # 5. Write updated matchup_stats back to each deck
    # ------------------------------------------------------------------
    updated = 0
    skipped = 0

    for deck in decks:
        if deck.id not in global_acc:
            continue

        g = global_acc[deck.id]
        wins = g["wins"]
        losses = g["losses"]
        total = wins + losses

        if total == 0:
            skipped += 1
            continue

        global_winrate = round(wins / total * 100, 2)
        meta_share = round(total / total_appearances * 100, 2) if total_appearances else 0.0

        # Build per-matchup dict
        matchups_out: dict[str, dict] = {}
        for opp_id, mu in matchup_acc[deck.id].items():
            mu_wins = mu["wins"]
            mu_losses = mu["losses"]
            mu_total = mu_wins + mu_losses
            if mu_total == 0:
                continue
            mu_winrate = round(mu_wins / mu_total * 100, 2)
            matchups_out[str(opp_id)] = {
                "wins": mu_wins,
                "losses": mu_losses,
                "sample_size": mu_total,
                "winrate": mu_winrate,
                "top_1000_winrate": mu_winrate,  # same data source for now
                "last_updated": now_iso,
            }

        # Merge: preserve existing oracle_cache / any other extra keys,
        # then overwrite the stats keys.
        deck.matchup_stats = {
            **deck.matchup_stats,
            "wins": wins,
            "losses": losses,
            "sample_size": total,
            "global_winrate": global_winrate,
            "meta_share": meta_share,
            "matchups": matchups_out,
        }
        deck.updated_at = datetime.now(timezone.utc)
        updated += 1

    await session.commit()
    log.info(
        "Done. Updated %d decks, skipped %d (no battles found).",
        updated,
        skipped,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        await compute_stats(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
