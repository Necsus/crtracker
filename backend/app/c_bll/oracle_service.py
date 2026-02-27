"""Business Logic Layer for Oracle Matchup Analysis.

Orchestrates the Oracle functionality, caching, and data transformation.
"""

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.deck_dal import DeckDAL
from app.d_llm.oracle_provider import OracleProvider
from app.schemas import (
    DeckResponse,
    OracleAdvice,
    OracleMatchupResponse,
    OracleRequest,
)


class OracleService:
    """Service for Oracle matchup analysis.

    Manages the generation and caching of tactical advice
    for deck matchups.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the Oracle service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.deck_dal = DeckDAL(session)
        self.oracle_provider = OracleProvider()

    # ==========================================================================
    # ORACLE ANALYSIS
    # ==========================================================================

    async def analyze_matchup(
        self,
        player_deck_id: int,
        opponent_deck_id: int,
        force_refresh: bool = False,
    ) -> OracleMatchupResponse | None:
        """Analyze a matchup and return Oracle advice.

        Args:
            player_deck_id: Player's deck ID
            opponent_deck_id: Opponent's deck ID
            force_refresh: Force regeneration instead of using cache

        Returns:
            Oracle matchup response or None if decks not found
        """
        # Fetch both decks
        player_deck = await self.deck_dal.get_by_id(player_deck_id)
        opponent_deck = await self.deck_dal.get_by_id(opponent_deck_id)

        if not player_deck or not opponent_deck:
            return None

        # Check cache first (unless refresh forced)
        if not force_refresh:
            cached = self._get_cached_analysis(player_deck, opponent_deck_id)
            if cached:
                return cached

        # Generate new analysis
        advice, winrate, difficulty = await self._generate_analysis(
            player_deck, opponent_deck
        )

        # Cache the results
        self._cache_analysis(
            player_deck, opponent_deck_id, advice, winrate, difficulty
        )

        # Build response
        return OracleMatchupResponse(
            player_deck=self._deck_to_response(player_deck),
            opponent_deck=self._deck_to_response(opponent_deck),
            winrate_prediction=winrate,
            difficulty=difficulty,
            advice=advice,
            generated_at=datetime.now(timezone.utc),
            source="llm",  # Will be "llm" in production, "mock" for MVP
        )

    async def _generate_analysis(
        self,
        player_deck,
        opponent_deck,
    ) -> tuple[list[OracleAdvice], float, str]:
        """Generate matchup analysis using the Oracle provider.

        Args:
            player_deck: Player deck ORM entity
            opponent_deck: Opponent deck ORM entity

        Returns:
            Tuple of (advice list, winrate prediction, difficulty)
        """
        # Extract card IDs
        player_cards = [
            card["id"] for card in player_deck.cards.get("cards", [])
        ]
        opponent_cards = [
            card["id"] for card in opponent_deck.cards.get("cards", [])
        ]

        # Call the Oracle provider
        return await self.oracle_provider.generate_matchup_advice(
            player_deck_name=player_deck.name,
            opponent_deck_name=opponent_deck.name,
            player_archetype=player_deck.archetype,
            opponent_archetype=opponent_deck.archetype,
            player_cards=player_cards,
            opponent_cards=opponent_cards,
        )

    def _get_cached_analysis(
        self,
        player_deck,
        opponent_deck_id: int,
    ) -> OracleMatchupResponse | None:
        """Retrieve cached Oracle analysis.

        Args:
            player_deck: Player deck ORM entity
            opponent_deck_id: Opponent deck ID

        Returns:
            Cached response or None
        """
        cached_data = self.deck_dal.get_oracle_cache(player_deck, opponent_deck_id)
        if not cached_data:
            return None

        # Check if cache is still valid (24 hours)
        cached_at = datetime.fromisoformat(cached_data.get("generated_at", ""))
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age > 86400:  # 24 hours
            return None

        # Reconstruct response from cache
        # In production, we'd cache the full response
        return None  # For MVP, regenerate each time

    def _cache_analysis(
        self,
        player_deck,
        opponent_deck_id: int,
        advice: list[OracleAdvice],
        winrate: float,
        difficulty: str,
    ) -> None:
        """Cache the Oracle analysis for future requests.

        Args:
            player_deck: Player deck ORM entity
            opponent_deck_id: Opponent deck ID
            advice: Generated advice list
            winrate: Winrate prediction
            difficulty: Difficulty rating
        """
        cache_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "winrate_prediction": winrate,
            "difficulty": difficulty,
            "advice_count": len(advice),
            # In production, cache full advice
        }

        # Schedule cache update (async)
        import asyncio

        asyncio.create_task(
            self.deck_dal.update_oracle_cache(
                player_deck.id, opponent_deck_id, cache_data
            )
        )

    # ==========================================================================
    # DATA TRANSFORMATION
    # ==========================================================================

    def _deck_to_response(self, deck) -> DeckResponse:
        """Transform ORM Deck to API response.

        Args:
            deck: Deck ORM entity

        Returns:
            DeckResponse schema
        """
        cards_data = deck.cards.get("cards", [])

        return DeckResponse(
            id=deck.id,
            name=deck.name,
            archetype=deck.archetype,
            cards=cards_data,
            avg_elixir=deck.avg_elixir,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )
