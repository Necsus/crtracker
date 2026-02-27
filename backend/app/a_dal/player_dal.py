"""Data Access Layer for Player-related operations.

Handles importing player data from external sources (mocked for MVP).
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.deck_dal import DeckDAL
from app.b_models.deck import Deck


class PlayerDAL:
    """DAL for Player operations.

    Handles player profile lookup and deck import from player tags.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the Player DAL.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.deck_dal = DeckDAL(session)

    # ==========================================================================
    # MOCK DATA - In production, this would call Supercell API
    # ==========================================================================

    async def get_player_profile(self, player_tag: str) -> dict | None:
        """Get player profile from Supercell API (mocked for MVP).

        Args:
            player_tag: Player tag (with or without # prefix)

        Returns:
            Mock player profile dict or None
        """
        # Normalize tag
        normalized_tag = player_tag.lstrip("#")

        # Mock database of players
        mock_players = {
            "2YJ08Y9": {
                "tag": "#2YJ08Y9",
                "name": "CWM arriving",
                "trophies": 8547,
                "best_trophies": 8721,
                "arena": "Champion",
                "wins": 15482,
                "losses": 11234,
                "current_deck": [
                    {
                        "id": "golem",
                        "name": "Golem",
                        "elixir": 8,
                        "rarity": "epic",
                        "type": "troop",
                        "icon_url": "/cards/golem.png",
                    },
                    {
                        "id": "witch",
                        "name": "Witch",
                        "elixir": 5,
                        "rarity": "epic",
                        "type": "troop",
                        "icon_url": "/cards/witch.png",
                    },
                    {
                        "id": "night-witch",
                        "name": "Night Witch",
                        "elixir": 4,
                        "rarity": "legendary",
                        "type": "troop",
                        "icon_url": "/cards/night-witch.png",
                    },
                    {
                        "id": "megas-mercenary",
                        "name": "Mega Minion",
                        "elixir": 3,
                        "rarity": "rare",
                        "type": "troop",
                        "icon_url": "/cards/mega-minion.png",
                    },
                    {
                        "id": "lightning",
                        "name": "Lightning",
                        "elixir": 6,
                        "rarity": "epic",
                        "type": "spell",
                        "icon_url": "/cards/lightning.png",
                    },
                    {
                        "id": "tombstone",
                        "name": "Tombstone",
                        "elixir": 3,
                        "rarity": "rare",
                        "type": "building",
                        "icon_url": "/cards/tombstone.png",
                    },
                    {
                        "id": "log",
                        "name": "The Log",
                        "elixir": 2,
                        "rarity": "legendary",
                        "type": "spell",
                        "icon_url": "/cards/log.png",
                    },
                    {
                        "id": "arrows",
                        "name": "Arrows",
                        "elixir": 3,
                        "rarity": "common",
                        "type": "spell",
                        "icon_url": "/cards/arrows.png",
                    },
                ],
            },
            "8JJRRR9": {
                "tag": "#8JJRRR9",
                "name": "Mortar King",
                "trophies": 7234,
                "best_trophies": 7512,
                "arena": "Champion",
                "wins": 12450,
                "losses": 9876,
                "current_deck": [
                    {
                        "id": "mortar",
                        "name": "Mortar",
                        "elixir": 4,
                        "rarity": "common",
                        "type": "building",
                        "icon_url": "/cards/mortar.png",
                    },
                    {
                        "id": "goblin-gang",
                        "name": "Goblin Gang",
                        "elixir": 3,
                        "rarity": "common",
                        "type": "troop",
                        "icon_url": "/cards/goblin-gang.png",
                    },
                    {
                        "id": "goblin-barrel",
                        "name": "Goblin Barrel",
                        "elixir": 3,
                        "rarity": "epic",
                        "type": "spell",
                        "icon_url": "/cards/goblin-barrel.png",
                    },
                    {
                        "id": "princess",
                        "name": "Princess",
                        "elixir": 3,
                        "rarity": "legendary",
                        "type": "troop",
                        "icon_url": "/cards/princess.png",
                    },
                    {
                        "id": "ice-spirit",
                        "name": "Ice Spirit",
                        "elixir": 2,
                        "rarity": "common",
                        "type": "troop",
                        "icon_url": "/cards/ice-spirit.png",
                    },
                    {
                        "id": "knight",
                        "name": "Knight",
                        "elixir": 3,
                        "rarity": "common",
                        "type": "troop",
                        "icon_url": "/cards/knight.png",
                    },
                    {
                        "id": "fireball",
                        "name": "Fireball",
                        "elixir": 4,
                        "rarity": "rare",
                        "type": "spell",
                        "icon_url": "/cards/fireball.png",
                    },
                    {
                        "id": "rocket",
                        "name": "Rocket",
                        "elixir": 6,
                        "rarity": "rare",
                        "type": "spell",
                        "icon_url": "/cards/rocket.png",
                    },
                ],
            },
        }

        return mock_players.get(normalized_tag)

    async def import_player_deck(self, player_tag: str) -> Deck | None:
        """Import and save a deck from a player's profile.

        Args:
            player_tag: Player tag to import from

        Returns:
            Created/updated Deck entity or None if player not found
        """
        profile = await self.get_player_profile(player_tag)
        if not profile or not profile.get("current_deck"):
            return None

        # Calculate average elixir
        cards = profile["current_deck"]
        avg_elixir = sum(card["elixir"] for card in cards) / len(cards)

        # Determine archetype (simple heuristic for MVP)
        card_ids = [c["id"] for c in cards]
        archetype = self._detect_archetype(card_ids)

        # Create deck entity
        deck = Deck(
            name=f"{profile['name']}'s {archetype}",
            archetype=archetype,
            cards={"cards": cards},
            avg_elixir=avg_elixir,
            player_tag=player_tag.lstrip("#"),
            matchup_stats=self._generate_mock_matchup_stats(),
            created_at=datetime.now(timezone.utc),
        )

        return await self.deck_dal.create(deck)

    def _detect_archetype(self, card_ids: list[str]) -> str:
        """Detect deck archetype from card list (simple heuristic).

        Args:
            card_ids: List of card IDs in the deck

        Returns:
            Detected archetype name
        """
        card_set = set(card_ids)

        archetype_rules = {
            "Beatdown": ["golem", "giant", "pekka", "electro-giant", "golem-golemites"],
            "Control": ["mortar", "xbow", "miner"],
            "Siege": ["xbow", "mortar"],
            "Cycle": ["hog-rider", "wall-breakers", "goblin-barrel"],
            "Spell Bait": ["goblin-barrel", "princess", "ice-spirit"],
            "Bridge Spam": ["bandit", "night-witch", "bats"],
            "Midrange": ["hog-rider", "valkyrie", "musketeer"],
        }

        for archetype, keywords in archetype_rules.items():
            if any(card in card_set for card in keywords):
                return archetype

        return "Balanced"

    def _generate_mock_matchup_stats(self) -> dict:
        """Generate mock matchup statistics for imported decks.

        Returns:
            Mock matchup statistics dict
        """
        return {
            "global_winrate": 52.0,
            "meta_share": 8.5,
            "sample_size": 5420,
            "matchups": {},
        }
