"""Business Logic Layer for Deck operations.

Orchestrates data flow between routes and DAL, applying business rules.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.deck_dal import DeckDAL
from app.a_dal.player_dal import PlayerDAL
from app.b_models.deck import Deck
from app.schemas import (
    DeckListItem,
    DeckResponse,
    DeckStatsResponse,
    MatchupStats,
    PlayerImportResponse,
    PlayerProfile,
)


class DeckService:
    """Service for deck-related business logic.

    Handles deck operations, statistics aggregation, and data transformation
    between ORM models and API schemas.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the deck service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.deck_dal = DeckDAL(session)
        self.player_dal = PlayerDAL(session)

    # ==========================================================================
    # DECK RETRIEVAL
    # ==========================================================================

    async def get_deck_by_id(self, deck_id: int) -> DeckResponse | None:
        """Get a deck by ID with full details.

        Args:
            deck_id: Deck database ID

        Returns:
            Deck response or None if not found
        """
        deck = await self.deck_dal.get_by_id(deck_id)
        if not deck:
            return None
        return self._deck_to_response(deck)

    async def list_decks(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[DeckListItem], int]:
        """List all decks with pagination.

        Args:
            offset: Pagination offset
            limit: Maximum results

        Returns:
            Tuple of (deck list items, total count)
        """
        decks = await self.deck_dal.get_all(offset=offset, limit=limit)
        total = await self.deck_dal.count()

        items = [
            DeckListItem(
                id=deck.id,
                name=deck.name,
                archetype=deck.archetype,
                avg_elixir=deck.avg_elixir,
                card_count=8,  # Always 8 in CR
            )
            for deck in decks
        ]

        return items, total

    async def search_decks(
        self,
        query: str,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[DeckListItem], int]:
        """Search decks by name or archetype.

        Args:
            query: Search query string
            offset: Pagination offset
            limit: Maximum results

        Returns:
            Tuple of (matching deck list items, total count)
        """
        decks = await self.deck_dal.search_decks(query, offset, limit)
        total = len(decks)  # Simplified for MVP

        items = [
            DeckListItem(
                id=deck.id,
                name=deck.name,
                archetype=deck.archetype,
                avg_elixir=deck.avg_elixir,
                card_count=8,
            )
            for deck in decks
        ]

        return items, total

    async def get_popular_decks(self, limit: int = 10) -> Sequence[DeckListItem]:
        """Get most popular decks by meta share.

        Args:
            limit: Maximum number of decks

        Returns:
            List of popular deck items
        """
        decks = await self.deck_dal.get_popular_decks(limit)

        return [
            DeckListItem(
                id=deck.id,
                name=deck.name,
                archetype=deck.archetype,
                avg_elixir=deck.avg_elixir,
                card_count=8,
            )
            for deck in decks
        ]

    # ==========================================================================
    # DECK STATISTICS
    # ==========================================================================

    async def get_deck_statistics(self, deck_id: int) -> DeckStatsResponse | None:
        """Get complete statistics for a deck including all matchups.

        Args:
            deck_id: Deck database ID

        Returns:
            Complete deck statistics or None if deck not found
        """
        deck = await self.deck_dal.get_by_id(deck_id)
        if not deck:
            return None

        # Build response
        deck_response = self._deck_to_response(deck)
        matchups = self._extract_matchup_stats(deck)

        return DeckStatsResponse(
            deck=deck_response,
            matchups=matchups,
            global_winrate=deck.global_winrate or 50.0,
            meta_share=deck.meta_share or 0.0,
        )

    def _extract_matchup_stats(self, deck: Deck) -> list[MatchupStats]:
        """Extract and format matchup statistics from deck JSONB.

        Args:
            deck: Deck entity with matchup_stats

        Returns:
            List of matchup statistics
        """
        matchups_data = deck.matchup_stats.get("matchups", {})
        matchups = []

        # In production, we'd fetch opponent deck names from DB
        # For MVP, we use mock data
        mock_opponents = {
            "2": {"name": "Hog Cycle", "archetype": "Cycle"},
            "3": {"name": "Log Bait", "archetype": "Spell Bait"},
            "4": {"name": "Golem Beatdown", "archetype": "Beatdown"},
            "5": {"name": "XBow Siege", "archetype": "Siege"},
            "6": {"name": "Graveyard Control", "archetype": "Control"},
            "7": {"name": "Pekka Bridge Spam", "archetype": "Bridge Spam"},
            "8": {"name": "Balloon Cycle", "archetype": "Cycle"},
            "9": {"name": "Elite Barbs", "archetype": "Beatdown"},
            "10": {"name": "Mortar Control", "archetype": "Siege"},
        }

        for opponent_id, stats in matchups_data.items():
            opponent_info = mock_opponents.get(
                opponent_id, {"name": f"Deck {opponent_id}", "archetype": "Unknown"}
            )

            matchups.append(
                MatchupStats(
                    opponent_deck_id=int(opponent_id),
                    opponent_deck_name=opponent_info["name"],
                    opponent_archetype=opponent_info["archetype"],
                    winrate=stats.get("winrate", 50.0),
                    sample_size=stats.get("sample_size", 0),
                    top_1000_winrate=stats.get("top_1000_winrate", 50.0),
                    last_updated=datetime.fromisoformat(
                        stats.get("last_updated", datetime.now(timezone.utc).isoformat())
                    ),
                )
            )

        # Sort by sample size (most played matchups first)
        matchups.sort(key=lambda m: m.sample_size, reverse=True)

        return matchups

    # ==========================================================================
    # PLAYER IMPORT
    # ==========================================================================

    async def import_player_deck(self, player_tag: str) -> PlayerImportResponse:
        """Import a deck from a player profile.

        Args:
            player_tag: Clash Royale player tag

        Returns:
            Import response with player profile and deck
        """
        profile_data = await self.player_dal.get_player_profile(player_tag)

        if not profile_data:
            return PlayerImportResponse(
                player=PlayerProfile(
                    tag=player_tag,
                    name="Unknown",
                    trophies=0,
                    best_trophies=0,
                    arena="Unknown",
                    wins=0,
                    losses=0,
                ),
                deck=None,
                message="Player not found. Check the tag and try again.",
            )

        # Try to import/create deck
        deck = await self.player_dal.import_player_deck(player_tag)

        player = PlayerProfile(
            tag=profile_data["tag"],
            name=profile_data["name"],
            trophies=profile_data["trophies"],
            best_trophies=profile_data["best_trophies"],
            arena=profile_data["arena"],
            wins=profile_data["wins"],
            losses=profile_data["losses"],
            current_deck=profile_data.get("current_deck"),
        )

        deck_response = self._deck_to_response(deck) if deck else None

        return PlayerImportResponse(
            player=player,
            deck=deck_response,
            message=f"Successfully imported deck for {player.name}!",
        )

    # ==========================================================================
    # DATA TRANSFORMATION HELPERS
    # ==========================================================================

    def _deck_to_response(self, deck: Deck) -> DeckResponse:
        """Transform ORM Deck entity to API response schema.

        Args:
            deck: Deck ORM entity

        Returns:
            DeckResponse schema
        """
        # Extract cards from JSONB
        cards_data = deck.cards.get("cards", [])

        return DeckResponse(
            id=deck.id,
            name=deck.name,
            archetype=deck.archetype,
            cards=cards_data,  # Already in correct format
            avg_elixir=deck.avg_elixir,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )
