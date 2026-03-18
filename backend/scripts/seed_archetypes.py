"""Seed script — Timeless ("Indemodable") Clash Royale archetypes.

Inserts the curated catalogue of archetypes whose structural identity has
persisted across many seasons.  These are the *only* archetypes that must be
hand-crafted; meta status (DOMINANT / VIABLE / …) is computed automatically
from battles by season.

Usage
-----
From the backend/ directory with the venv activated::

    python -m scripts.seed_archetypes           # dry-run preview
    python -m scripts.seed_archetypes --commit   # actually write to the DB

Card ID resolution
------------------
``core_cards`` must contain the **same id format** that is stored in
``decks.cards[].id``.  The script resolves human-readable card names to their
integer CR API card_id via the ``cards`` table (populated by sync_cards).
If a card is not yet in the DB (mock-data-only environment), it falls back to
a kebab-slug of the card name ("Hog Rider" → "hog-rider").

Idempotency
-----------
Archetypes are upserted by **name** (unique constraint).  Re-running the
script will update existing rows without creating duplicates.
"""

from __future__ import annotations

import asyncio
import logging
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.database import async_session_maker  # noqa: E402
from app.b_models.archetype import Archetype  # noqa: E402
# Register all models so SA mapper is fully initialised
from app.b_models.battle import Battle          # noqa: E402, F401
from app.b_models.card import Card as CardModel  # noqa: E402
from app.b_models.deck import Deck              # noqa: E402, F401
from app.b_models.deck_meta_status import DeckMetaStatus  # noqa: E402, F401
from app.b_models.player import Player          # noqa: E402, F401
from app.b_models.player_season_rank import PlayerSeasonRank  # noqa: E402, F401
from app.b_models.season import Season          # noqa: E402, F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ===========================================================================
# Archetype catalogue
# ===========================================================================
# Each entry has:
#   name         – unique display name (used as upsert key)
#   parent       – name of the parent archetype (None for root)
#   win_condition – slug of the primary win-condition card
#   play_style   – one of CYCLE / BEATDOWN / CONTROL / BRIDGE_SPAM / SIEGE / HYBRID
#   is_timeless  – always True in this seed (this is the whole point)
#   core_cards   – human-readable card names; resolved to DB ids at runtime
#   description  – optional flavour text
# ===========================================================================

ARCHETYPES: list[dict] = [

    # ── HOG CYCLE ────────────────────────────────────────────────────────────
    {
        "name": "Hog Cycle",
        "parent": None,
        "win_condition": "hog-rider",
        "play_style": "CYCLE",
        "is_timeless": True,
        "core_cards": ["Hog Rider"],
        "description": (
            "Family of fast-cycle decks built around the Hog Rider.  "
            "Relies on relentless pressure and having the Hog arrive before the "
            "opponent can react.  Average elixir typically sits between 2.6 and 3.3."
        ),
    },
    {
        "name": "Hog 2.6",
        "parent": "Hog Cycle",
        "win_condition": "hog-rider",
        "play_style": "CYCLE",
        "is_timeless": True,
        "core_cards": ["Hog Rider", "Ice Golem", "Ice Spirit", "Musketeer", "Cannon"],
        "description": (
            "The most iconic 2.6-average-elixir deck.  Ice Golem + Ice Spirit cycle "
            "the Hog back every 3–4 seconds.  Cannon provides a reliable defence "
            "against ground pushes while Musketeer handles air threats."
        ),
    },
    {
        "name": "Hog 3.0",
        "parent": "Hog Cycle",
        "win_condition": "hog-rider",
        "play_style": "CYCLE",
        "is_timeless": True,
        "core_cards": ["Hog Rider", "Ice Golem", "Ice Spirit", "Musketeer"],
        "description": (
            "Slightly heavier Hog Cycle variant (avg ~3.0) that swaps the Cannon "
            "for a more offensive slot.  Shares the same Ice Golem + Ice Spirit "
            "cycling core as Hog 2.6."
        ),
    },

    # ── LOG BAIT ─────────────────────────────────────────────────────────────
    {
        "name": "Log Bait",
        "parent": None,
        "win_condition": "goblin-barrel",
        "play_style": "CYCLE",
        "is_timeless": True,
        "core_cards": ["Goblin Barrel", "Princess"],
        "description": (
            "Forces the opponent to use their small spells (Log, Zap) on goblins "
            "or the Princess, leaving the Goblin Barrel unopposed.  Rocket serves "
            "as secondary win condition and tower chip."
        ),
    },
    {
        "name": "Log Bait Classic",
        "parent": "Log Bait",
        "win_condition": "goblin-barrel",
        "play_style": "CYCLE",
        "is_timeless": True,
        "core_cards": ["Goblin Barrel", "Goblin Gang", "Princess", "Rocket", "Knight"],
        "description": (
            "The original Log Bait shell: Knight as a cheap tank, Goblin Gang to "
            "bait Arrows, Princess to bait the Log, Goblin Barrel as win condition, "
            "Rocket to out-chip the tower.  Perennial ladder staple."
        ),
    },

    # ── X-BOW SIEGE ──────────────────────────────────────────────────────────
    {
        "name": "X-Bow Siege",
        "parent": None,
        "win_condition": "x-bow",
        "play_style": "SIEGE",
        "is_timeless": True,
        "core_cards": ["X-Bow"],
        "description": (
            "Family of decks that protect an X-Bow planted at the bridge.  Pure "
            "defensive cycle: delay the opponent's push long enough for the "
            "X-Bow to deal lethal tower damage.  Patience and timing are everything."
        ),
    },
    {
        "name": "X-Bow 3.0",
        "parent": "X-Bow Siege",
        "win_condition": "x-bow",
        "play_style": "SIEGE",
        "is_timeless": True,
        "core_cards": ["X-Bow", "Tesla", "Ice Spirit", "Skeletons", "The Log"],
        "description": (
            "The classic 3.0-average-elixir X-Bow build.  Tesla acts as the "
            "primary defensive tower, Ice Spirit + Skeletons provide cheap cycle "
            "and distraction, The Log clears small swarms.  Extreme efficiency."
        ),
    },
    {
        "name": "X-Bow 4.0",
        "parent": "X-Bow Siege",
        "win_condition": "x-bow",
        "play_style": "SIEGE",
        "is_timeless": True,
        "core_cards": ["X-Bow", "Tesla", "Knight", "Ice Golem"],
        "description": (
            "Heavier X-Bow variant with Knight and Ice Golem for tankier defence "
            "and a slower, more controlling play style.  Trades pure cycle speed "
            "for better survivability against beatdown."
        ),
    },

    # ── MORTAR CYCLE ─────────────────────────────────────────────────────────
    {
        "name": "Mortar Cycle",
        "parent": None,
        "win_condition": "mortar",
        "play_style": "SIEGE",
        "is_timeless": True,
        "core_cards": ["Mortar", "Goblin Gang", "Princess"],
        "description": (
            "Budget siege deck built around the Mortar.  Goblin Gang and Princess "
            "bait out spells and defend cheaply while the Mortar chips the tower. "
            "Rocket closes out the game.  Loved by free-to-play players."
        ),
    },

    # ── GOLEM BEATDOWN ────────────────────────────────────────────────────────
    {
        "name": "Golem Beatdown",
        "parent": None,
        "win_condition": "golem",
        "play_style": "BEATDOWN",
        "is_timeless": True,
        "core_cards": ["Golem"],
        "description": (
            "Elixir-heavy beatdown that builds an unstoppable push behind a Golem. "
            "Support troops (Night Witch, Baby Dragon, Mega Minion…) shred through "
            "any defence.  Lightning spell disables key defensive buildings."
        ),
    },
    {
        "name": "Golem Night Witch",
        "parent": "Golem Beatdown",
        "win_condition": "golem",
        "play_style": "BEATDOWN",
        "is_timeless": True,
        "core_cards": ["Golem", "Night Witch", "Lightning", "Mega Minion"],
        "description": (
            "The defining Golem Beatdown variant.  Night Witch spawns a constant "
            "stream of bats that both protect the push and deal damage.  "
            "Lightning resets defences and deals massive chip damage."
        ),
    },
    {
        "name": "Golem Lumberjack",
        "parent": "Golem Beatdown",
        "win_condition": "golem",
        "play_style": "BEATDOWN",
        "is_timeless": True,
        "core_cards": ["Golem", "Lumberjack", "Night Witch"],
        "description": (
            "Golem variant that replaces Lightning with Lumberjack for more "
            "consistent rage generation.  The Rage spell dropped by the dying "
            "Lumberjack dramatically accelerates the Golem and support troops."
        ),
    },

    # ── LAVALOON ─────────────────────────────────────────────────────────────
    {
        "name": "LavaLoon",
        "parent": None,
        "win_condition": "lava-hound",
        "play_style": "HYBRID",
        "is_timeless": True,
        "core_cards": ["Lava Hound", "Balloon"],
        "description": (
            "Dual-threat air beatdown.  The Lava Hound tanks all anti-air while "
            "the Balloon destroys the tower.  Lava Pups left after the Hound dies "
            "clean up remaining defenders.  Countered by a well-timed Freeze."
        ),
    },
    {
        "name": "LavaLoon Tombstone",
        "parent": "LavaLoon",
        "win_condition": "lava-hound",
        "play_style": "HYBRID",
        "is_timeless": True,
        "core_cards": ["Lava Hound", "Balloon", "Tombstone"],
        "description": (
            "Classic LavaLoon variant that uses Tombstone at the bridge as an "
            "additional defensive anchor and distraction during the push cycle."
        ),
    },
    {
        "name": "LavaLoon Freeze",
        "parent": "LavaLoon",
        "win_condition": "lava-hound",
        "play_style": "HYBRID",
        "is_timeless": True,
        "core_cards": ["Lava Hound", "Balloon", "Freeze"],
        "description": (
            "Aggressive variant that trades defensive stability for a devastating "
            "Freeze spell to lock down the tower and any last-minute defenders when "
            "the Balloon connects."
        ),
    },

    # ── MINER CONTROL ────────────────────────────────────────────────────────
    {
        "name": "Miner Control",
        "parent": None,
        "win_condition": "miner",
        "play_style": "CONTROL",
        "is_timeless": True,
        "core_cards": ["Miner", "Poison"],
        "description": (
            "Slow, methodical control archetype.  Miner delivers consistent chip "
            "damage to the tower while Poison clears defensive troops and forces "
            "the opponent to play reactively.  Builds small elixir advantages "
            "over long games."
        ),
    },
    {
        "name": "Miner Poison Gang",
        "parent": "Miner Control",
        "win_condition": "miner",
        "play_style": "CONTROL",
        "is_timeless": True,
        "core_cards": ["Miner", "Poison", "Goblin Gang"],
        "description": (
            "Miner Control variant that pairs Poison with Goblin Gang to apply "
            "dual-lane pressure and force the opponent to split defensive resources."
        ),
    },

    # ── GRAVEYARD CONTROL ────────────────────────────────────────────────────
    {
        "name": "Graveyard Control",
        "parent": None,
        "win_condition": "graveyard",
        "play_style": "CONTROL",
        "is_timeless": True,
        "core_cards": ["Graveyard"],
        "description": (
            "Defensive control deck that stalls pushes with high-HP buildings and "
            "troops, then counters with a surprise Graveyard on the tower once the "
            "opponent is out of elixir.  Very high skill ceiling."
        ),
    },
    {
        "name": "Graveyard Poison",
        "parent": "Graveyard Control",
        "win_condition": "graveyard",
        "play_style": "CONTROL",
        "is_timeless": True,
        "core_cards": ["Graveyard", "Poison"],
        "description": (
            "The defining Graveyard variant.  Poison cast simultaneously with "
            "Graveyard eliminates defensive troops before they can kill the "
            "skeletons, guaranteeing tower damage."
        ),
    },

    # ── PEKKA BRIDGE SPAM ────────────────────────────────────────────────────
    {
        "name": "PEKKA Bridge Spam",
        "parent": None,
        "win_condition": "pekka",
        "play_style": "BRIDGE_SPAM",
        "is_timeless": True,
        "core_cards": ["P.E.K.K.A", "Bandit"],
        "description": (
            "Aggressive archetype that deploys high-damage troops directly at the "
            "bridge to deny the opponent the space to counter-push.  PEKKA tanks "
            "while fast flankers (Bandit, Battle Ram) deal damage.  "
            "Electro Wizard or Mega Knight provide air/swarm support."
        ),
    },
    {
        "name": "Classic PEKKA BS",
        "parent": "PEKKA Bridge Spam",
        "win_condition": "pekka",
        "play_style": "BRIDGE_SPAM",
        "is_timeless": True,
        "core_cards": ["P.E.K.K.A", "Bandit", "Battle Ram", "Electro Wizard"],
        "description": (
            "The original PEKKA Bridge Spam shell.  Battle Ram applies immediate "
            "bridge pressure, Bandit flanks and dodges spells, Electro Wizard resets "
            "Inferno Tower/Dragon.  High APM required to pilot optimally."
        ),
    },

    # ── GIANT BEATDOWN ───────────────────────────────────────────────────────
    {
        "name": "Giant Beatdown",
        "parent": None,
        "win_condition": "giant",
        "play_style": "BEATDOWN",
        "is_timeless": True,
        "core_cards": ["Giant"],
        "description": (
            "Beatdown built around the Giant as a sturdy, cheap-ish tank.  "
            "More accessible than Golem; avg elixir usually sits around 4.0–4.5.  "
            "Support troops vary widely — Double Prince and Witch are classic combos."
        ),
    },
    {
        "name": "Giant Double Prince",
        "parent": "Giant Beatdown",
        "win_condition": "giant",
        "play_style": "BEATDOWN",
        "is_timeless": True,
        "core_cards": ["Giant", "Prince", "Dark Prince"],
        "description": (
            "Classic Giant + Prince + Dark Prince tri-threat push.  "
            "Dark Prince clears swarms with his area damage, Prince deals massive "
            "single-target damage, Giant absorbs all defensive fire.  "
            "One of the oldest archetypes in Clash Royale."
        ),
    },
]


# ===========================================================================
# Card name → DB card_id resolver
# ===========================================================================

def _slugify(name: str) -> str:
    """Convert 'Hog Rider' → 'hog-rider', 'P.E.K.K.A' → 'p.e.k.k.a', etc."""
    return name.lower().replace(" ", "-")


async def _build_card_map(session: AsyncSession) -> dict[str, str]:
    """Return {card_name_lower: str(card_id)} from the cards table.

    Falls back to an empty dict if the table has no rows (mock-data env).
    """
    result = await session.execute(select(CardModel.card_id, CardModel.name))
    rows = result.all()
    if not rows:
        log.warning(
            "cards table is empty — core_cards will use kebab slug fallback. "
            "Run 'python -m scripts.sync_cards' first for production-accurate fingerprinting."
        )
    return {row.name.lower(): str(row.card_id) for row in rows}


def _resolve_core_cards(names: list[str], card_map: dict[str, str]) -> list[str]:
    """Translate human-readable card names to the id format stored in decks."""
    resolved = []
    for name in names:
        found = card_map.get(name.lower())
        if found:
            resolved.append(found)
        else:
            slug = _slugify(name)
            log.debug("Card '%s' not in DB — using slug fallback '%s'", name, slug)
            resolved.append(slug)
    return resolved


# ===========================================================================
# Upsert logic
# ===========================================================================

async def _get_or_none(session: AsyncSession, name: str) -> Archetype | None:
    result = await session.execute(
        select(Archetype).where(Archetype.name == name)
    )
    return result.scalar_one_or_none()


async def seed(session: AsyncSession, *, commit: bool) -> None:
    card_map = await _build_card_map(session)

    # Two-pass: insert roots first, then variants (need parent IDs).
    roots = [a for a in ARCHETYPES if a["parent"] is None]
    variants = [a for a in ARCHETYPES if a["parent"] is not None]

    inserted = 0
    updated = 0

    for entry in roots + variants:
        parent_id: int | None = None
        if entry["parent"]:
            parent = await _get_or_none(session, entry["parent"])
            if parent is None:
                log.error(
                    "Parent archetype '%s' not found for '%s' — skipping.",
                    entry["parent"],
                    entry["name"],
                )
                continue
            parent_id = parent.id

        core = _resolve_core_cards(entry["core_cards"], card_map)

        existing = await _get_or_none(session, entry["name"])
        if existing:
            existing.win_condition = entry["win_condition"]
            existing.play_style = entry["play_style"]
            existing.is_timeless = entry["is_timeless"]
            existing.variant_of_id = parent_id
            existing.core_cards = core
            existing.description = entry.get("description")
            updated += 1
            log.info("  UPDATED  %s", entry["name"])
        else:
            archetype = Archetype(
                name=entry["name"],
                win_condition=entry["win_condition"],
                play_style=entry["play_style"],
                is_timeless=entry["is_timeless"],
                variant_of_id=parent_id,
                core_cards=core,
                description=entry.get("description"),
            )
            session.add(archetype)
            await session.flush()  # materialise id for children
            inserted += 1
            log.info("  INSERTED %s", entry["name"])

    if commit:
        await session.commit()
        log.info("✔ Committed — %d inserted, %d updated.", inserted, updated)
    else:
        await session.rollback()
        log.info(
            "✔ Dry-run complete — %d would be inserted, %d would be updated. "
            "Pass --commit to persist.",
            inserted,
            updated,
        )


# ===========================================================================
# Entry point
# ===========================================================================

async def main() -> None:
    do_commit = "--commit" in sys.argv

    log.info(
        "Seeding timeless archetypes (%s)…",
        "COMMIT mode" if do_commit else "DRY-RUN — pass --commit to persist",
    )

    async with async_session_maker() as session:
        await seed(session, commit=do_commit)


if __name__ == "__main__":
    asyncio.run(main())
