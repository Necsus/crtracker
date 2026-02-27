"""Seed script for initial deck data.

Populates the database with mock deck and matchup data for MVP testing.
Run this after migrations: python -m alembic upgrade head && python app/alembic/seed_data.py
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.b_models.deck import Deck


# Mock card database
CARDS_DB = {
    # Troops
    "golem": {"id": "golem", "name": "Golem", "elixir": 8, "rarity": "epic", "type": "troop"},
    "witch": {"id": "witch", "name": "Witch", "elixir": 5, "rarity": "epic", "type": "troop"},
    "night-witch": {"id": "night-witch", "name": "Night Witch", "elixir": 4, "rarity": "legendary", "type": "troop"},
    "mega-minion": {"id": "mega-minion", "name": "Mega Minion", "elixir": 3, "rarity": "rare", "type": "troop"},
    "hog-rider": {"id": "hog-rider", "name": "Hog Rider", "elixir": 4, "rarity": "rare", "type": "troop"},
    "valkyrie": {"id": "valkyrie", "name": "Valkyrie", "elixir": 4, "rarity": "rare", "type": "troop"},
    "musketeer": {"id": "musketeer", "name": "Musketeer", "elixir": 4, "rarity": "rare", "type": "troop"},
    "ice-wizard": {"id": "ice-wizard", "name": "Ice Wizard", "elixir": 3, "rarity": "legendary", "type": "troop"},
    "electro-wizard": {"id": "electro-wizard", "name": "Electro Wizard", "elixir": 4, "rarity": "legendary", "type": "troop"},
    "knight": {"id": "knight", "name": "Knight", "elixir": 3, "rarity": "common", "type": "troop"},
    "archer-queen": {"id": "archer-queen", "name": "Archer Queen", "elixir": 5, "rarity": "legendary", "type": "troop"},
    "golden-knight": {"id": "golden-knight", "name": "Golden Knight", "elixir": 4, "rarity": "champion", "type": "troop"},
    "goblin-gang": {"id": "goblin-gang", "name": "Goblin Gang", "elixir": 3, "rarity": "common", "type": "troop"},
    "miner": {"id": "miner", "name": "Miner", "elixir": 3, "rarity": "rare", "type": "troop"},
    "pekka": {"id": "pekka", "name": "PEKKA", "elixir": 7, "rarity": "epic", "type": "troop"},
    "bandit": {"id": "bandit", "name": "Bandit", "elixir": 3, "rarity": "legendary", "type": "troop"},
    "skeleton-army": {"id": "skeleton-army", "name": "Skeleton Army", "elixir": 3, "rarity": "epic", "type": "troop"},
    "bats": {"id": "bats", "name": "Bats", "elixir": 2, "rarity": "common", "type": "troop"},
    "princess": {"id": "princess", "name": "Princess", "elixir": 3, "rarity": "legendary", "type": "troop"},
    "golemites": {"id": "golemites", "name": "Golemites", "elixir": 5, "rarity": "common", "type": "troop"},
    "elite-barbs": {"id": "elite-barbs", "name": "Elite Barbarians", "elixir": 6, "rarity": "common", "type": "troop"},
    "balloon": {"id": "balloon", "name": "Balloon", "elixir": 5, "rarity": "epic", "type": "troop"},
    "ice-spirit": {"id": "ice-spirit", "name": "Ice Spirit", "elixir": 1, "rarity": "common", "type": "troop"},
    # Spells
    "lightning": {"id": "lightning", "name": "Lightning", "elixir": 6, "rarity": "epic", "type": "spell"},
    "log": {"id": "log", "name": "The Log", "elixir": 2, "rarity": "legendary", "type": "spell"},
    "arrows": {"id": "arrows", "name": "Arrows", "elixir": 3, "rarity": "common", "type": "spell"},
    "fireball": {"id": "fireball", "name": "Fireball", "elixir": 4, "rarity": "rare", "type": "spell"},
    "rocket": {"id": "rocket", "name": "Rocket", "elixir": 6, "rarity": "rare", "type": "spell"},
    "zap": {"id": "zap", "name": "Zap", "elixir": 2, "rarity": "common", "type": "spell"},
    "poison": {"id": "poison", "name": "Poison", "elixir": 4, "rarity": "epic", "type": "spell"},
    "rage": {"id": "rage", "name": "Rage", "elixir": 2, "rarity": "epic", "type": "spell"},
    "clone": {"id": "clone", "name": "Clone", "elixir": 3, "rarity": "epic", "type": "spell"},
    "freeze": {"id": "freeze", "name": "Freeze", "elixir": 4, "rarity": "epic", "type": "spell"},
    # Buildings
    "tombstone": {"id": "tombstone", "name": "Tombstone", "elixir": 3, "rarity": "rare", "type": "building"},
    "furnace": {"id": "furnace", "name": "Furnace", "elixir": 4, "rarity": "rare", "type": "building"},
    "xbow": {"id": "xbow", "name": "X-Bow", "elixir": 6, "rarity": "epic", "type": "building"},
    "mortar": {"id": "mortar", "name": "Mortar", "elixir": 4, "rarity": "common", "type": "building"},
    "inferno-tower": {"id": "inferno-tower", "name": "Inferno Tower", "elixir": 5, "rarity": "rare", "type": "building"},
    "cannon": {"id": "cannon", "name": "Cannon", "elixir": 3, "rarity": "common", "type": "building"},
    "tesla": {"id": "tesla", "name": "Tesla", "elixir": 4, "rarity": "common", "type": "building"},
    "bomb-tower": {"id": "bomb-tower", "name": "Bomb Tower", "elixir": 4, "rarity": "rare", "type": "building"},
    "goblin-hut": {"id": "goblin-hut", "name": "Goblin Hut", "elixir": 5, "rarity": "rare", "type": "building"},
}


# Mock deck definitions
MOCK_DECKS = [
    {
        "name": "Classic Golem Beatdown",
        "archetype": "Beatdown",
        "cards": ["golem", "witch", "night-witch", "mega-minion", "lightning", "tombstone", "log", "arrows"],
        "meta_share": 12.5,
        "global_winrate": 52.3,
    },
    {
        "name": "Hog 2.6 Cycle",
        "archetype": "Cycle",
        "cards": ["hog-rider", "ice-wizard", "musketeer", "furnace", "log", "zap", "cannon", "skeleton-army"],
        "meta_share": 15.8,
        "global_winrate": 50.1,
    },
    {
        "name": "Log Bait",
        "archetype": "Spell Bait",
        "cards": ["goblin-gang", "princess", "log", "tombstone", "bats", "rocket", "knight", "ice-wizard"],
        "meta_share": 10.2,
        "global_winrate": 49.8,
    },
    {
        "name": "XBow Siege",
        "archetype": "Siege",
        "cards": ["xbow", "tesla", "archer-queen", "log", "arrows", "knight", "ice-wizard", "miner"],
        "meta_share": 8.5,
        "global_winrate": 47.5,
    },
    {
        "name": "Mortar Control",
        "archetype": "Siege",
        "cards": ["mortar", "goblin-gang", "princess", "log", "rocket", "knight", "fireball", "zap"],
        "meta_share": 6.3,
        "global_winrate": 46.2,
    },
    {
        "name": "Pekka Bridge Spam",
        "archetype": "Bridge Spam",
        "cards": ["pekka", "electro-wizard", "bandit", "musketeer", "log", "fireball", "ice-wizard", "knight"],
        "meta_share": 11.4,
        "global_winrate": 51.7,
    },
    {
        "name": "Graveyard Control",
        "archetype": "Control",
        "cards": ["witch", "night-witch", "mega-minion", "poison", "tombstone", "log", "arrows", "ice-wizard"],
        "meta_share": 9.1,
        "global_winrate": 50.5,
    },
    {
        "name": "Elite Barbs Beatdown",
        "archetype": "Beatdown",
        "cards": ["elite-barbs", "bandit", "musketeer", "log", "fireball", "zap", "knight", "skeleton-army"],
        "meta_share": 7.8,
        "global_winrate": 48.9,
    },
    {
        "name": "Balloon Cycle",
        "archetype": "Cycle",
        "cards": ["balloon", "mega-minion", "bats", "log", "arrows", "tombstone", "miner", "skeleton-army"],
        "meta_share": 8.7,
        "global_winrate": 49.2,
    },
    {
        "name": "Golem Lightning",
        "archetype": "Beatdown",
        "cards": ["golem", "mega-minion", "electro-wizard", "lightning", "log", "tombstone", "arrows", "knight"],
        "meta_share": 9.9,
        "global_winrate": 53.1,
    },
]


def calculate_avg_elixir(card_ids: list[str]) -> float:
    """Calculate average elixir cost of a deck."""
    total = sum(CARDS_DB[cid]["elixir"] for cid in card_ids)
    return round(total / len(card_ids), 1)


def generate_matchup_stats(deck_index: int) -> dict:
    """Generate mock matchup statistics for a deck."""
    # Winrates against other decks (deck_id as key)
    # This simulates realistic matchup spreads
    matchups = {
        "2": {"winrate": 58.2, "top_1000_winrate": 60.1, "sample_size": 3420, "last_updated": datetime.now(timezone.utc).isoformat()},
        "3": {"winrate": 45.5, "top_1000_winrate": 47.2, "sample_size": 2890, "last_updated": datetime.now(timezone.utc).isoformat()},
        "4": {"winrate": 52.8, "top_1000_winrate": 54.5, "sample_size": 1980, "last_updated": datetime.now(timezone.utc).isoformat()},
        "5": {"winrate": 61.2, "top_1000_winrate": 63.0, "sample_size": 1650, "last_updated": datetime.now(timezone.utc).isoformat()},
        "6": {"winrate": 49.5, "top_1000_winrate": 50.8, "sample_size": 2450, "last_updated": datetime.now(timezone.utc).isoformat()},
        "7": {"winrate": 55.3, "top_1000_winrate": 57.1, "sample_size": 2130, "last_updated": datetime.now(timezone.utc).isoformat()},
        "8": {"winrate": 47.8, "top_1000_winrate": 49.2, "sample_size": 1780, "last_updated": datetime.now(timezone.utc).isoformat()},
        "9": {"winrate": 53.5, "top_1000_winrate": 55.3, "sample_size": 1560, "last_updated": datetime.now(timezone.utc).isoformat()},
        "10": {"winrate": 51.2, "top_1000_winrate": 52.8, "sample_size": 1890, "last_updated": datetime.now(timezone.utc).isoformat()},
    }

    return {
        "global_winrate": MOCK_DECKS[deck_index]["global_winrate"],
        "meta_share": MOCK_DECKS[deck_index]["meta_share"],
        "sample_size": 12450,
        "matchups": matchups,
    }


async def seed_database() -> None:
    """Seed the database with initial mock data."""
    async with async_session_maker() as session:
        # Check if data already exists
        from sqlalchemy import select
        existing = await session.execute(select(Deck).limit(1))
        if existing.scalars().first():
            print("Database already seeded. Skipping...")
            return

        print("Seeding database with mock decks...")

        for idx, deck_data in enumerate(MOCK_DECKS, start=1):
            cards = [CARDS_DB[cid] for cid in deck_data["cards"]]
            avg_elixir = calculate_avg_elixir(deck_data["cards"])

            deck = Deck(
                name=deck_data["name"],
                archetype=deck_data["archetype"],
                cards={"cards": cards},
                avg_elixir=avg_elixir,
                player_tag=None,
                matchup_stats=generate_matchup_stats(idx - 1),
                oracle_cache={},
                created_at=datetime.now(timezone.utc),
            )

            session.add(deck)
            print(f"  Created deck: {deck.name} ({deck.archetype}) - {avg_elixir} avg elixir")

        await session.commit()
        print(f"Seeded {len(MOCK_DECKS)} decks successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
