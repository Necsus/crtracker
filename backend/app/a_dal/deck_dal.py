"""Data Access Layer for Deck entities.

Handles all database operations related to decks and their matchups.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Result, Select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.base_dal import BaseDAL
from app.b_models.deck import Deck


class DeckDAL(BaseDAL[Deck]):
    """DAL for Deck operations.

    Extends BaseDAL with deck-specific queries including
    archetype search, player tag lookup, and matchup data extraction.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the Deck DAL.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Deck)

    # ==========================================================================
    # DECK QUERIES
    # ==========================================================================

    async def get_by_archetype(
        self,
        archetype: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Deck]:
        """Get all decks of a specific archetype.

        Args:
            archetype: Archetype name to filter by
            offset: Pagination offset
            limit: Maximum results to return

        Returns:
            List of decks matching the archetype
        """
        stmt = (
            select(Deck)
            .where(Deck.archetype.ilike(f"%{archetype}%"))
            .offset(offset)
            .limit(limit)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_player_tag(self, player_tag: str) -> Deck | None:
        """Get the most recent deck for a player tag.

        Args:
            player_tag: Player tag (format: #ABC123DE or ABC123DE)

        Returns:
            Latest deck for the player or None
        """
        # Normalize player tag (remove # if present)
        normalized_tag = player_tag.lstrip("#")

        stmt = (
            select(Deck)
            .where(Deck.player_tag == normalized_tag)
            .order_by(Deck.created_at.desc())
            .limit(1)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search_decks(
        self,
        query: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Deck]:
        """Search decks by name or archetype.

        Args:
            query: Search query string
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of matching decks
        """
        stmt = (
            select(Deck)
            .where(
                or_(
                    Deck.name.ilike(f"%{query}%"),
                    Deck.archetype.ilike(f"%{query}%"),
                )
            )
            .offset(offset)
            .limit(limit)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_popular_decks(
        self,
        limit: int = 10,
    ) -> Sequence[Deck]:
        """Get most popular decks based on meta share.

        Args:
            limit: Maximum number of decks to return

        Returns:
            List of decks ordered by meta share
        """
        stmt = (
            select(Deck)
            .order_by(Deck.matchup_stats["meta_share"].desc())  # type: ignore
            .limit(limit)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    # ==========================================================================
    # MATCHUP DATA EXTRACTION
    # ==========================================================================

    def get_matchup_stats(self, deck: Deck, opponent_deck_id: int) -> dict | None:
        """Extract matchup stats for a specific opponent from deck JSONB.

        This is a synchronous helper that operates on the already-loaded deck entity.
        The data is extracted from the JSONB matchup_stats field.

        Args:
            deck: Deck entity with loaded matchup_stats
            opponent_deck_id: ID of the opponent deck

        Returns:
            Matchup statistics dict or None if not found
        """
        matchups = deck.matchup_stats.get("matchups", {})
        return matchups.get(str(opponent_deck_id))

    async def update_matchup_cache(
        self,
        deck_id: int,
        opponent_deck_id: int,
        stats: dict,
    ) -> None:
        """Update the cached matchup statistics for a deck pair.

        This updates the JSONB field with new matchup data.

        Args:
            deck_id: Player deck ID
            opponent_deck_id: Opponent deck ID
            stats: Matchup statistics to cache
        """
        deck = await self.get_by_id(deck_id)
        if not deck:
            return

        # Initialize matchups dict if needed
        if "matchups" not in deck.matchup_stats:
            deck.matchup_stats["matchups"] = {}

        # Update the specific matchup
        deck.matchup_stats["matchups"][str(opponent_deck_id)] = stats

        # Mark as updated
        from datetime import datetime, timezone

        deck.updated_at = datetime.now(timezone.utc)

        # Session will commit on scope exit

    async def update_oracle_cache(
        self,
        deck_id: int,
        opponent_deck_id: int,
        oracle_data: dict,
    ) -> None:
        """Update the cached Oracle advice for a deck pair.

        Args:
            deck_id: Player deck ID
            opponent_deck_id: Opponent deck ID
            oracle_data: Oracle analysis results to cache
        """
        deck = await self.get_by_id(deck_id)
        if not deck:
            return

        # Initialize oracle cache if needed
        if not deck.oracle_cache:
            deck.oracle_cache = {}

        # Store the oracle data
        deck.oracle_cache[str(opponent_deck_id)] = oracle_data

        # Mark as updated
        from datetime import datetime, timezone

        deck.updated_at = datetime.now(timezone.utc)

    def get_oracle_cache(
        self,
        deck: Deck,
        opponent_deck_id: int,
    ) -> dict | None:
        """Retrieve cached Oracle advice for a matchup.

        Args:
            deck: Deck entity with loaded oracle_cache
            opponent_deck_id: Opponent deck ID

        Returns:
            Cached oracle data or None if not cached
        """
        return deck.oracle_cache.get(str(opponent_deck_id))
