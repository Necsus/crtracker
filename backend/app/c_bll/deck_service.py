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

    @staticmethod
    def _extract_cards(raw: Any) -> list[dict]:
        """Normalize cards from either storage format into a clean list.

        Supported formats:
        - Plain list: [{"id": ..., "elixir": ..., "rarity": "Rare", ...}, ...]
        - Dict wrapper (seed data): {"cards": [...]}

        Rarity is lowercased to satisfy the Pydantic Literal constraint.
        Cards with missing required fields are silently dropped.
        """
        if isinstance(raw, dict):
            raw = raw.get("cards", [])
        if not isinstance(raw, list):
            return []

        result = []
        for c in raw:
            if not isinstance(c, dict):
                continue
            card_id = c.get("id")
            name = c.get("name")
            elixir = c.get("elixir") if c.get("elixir") is not None else c.get("elixirCost")
            rarity = c.get("rarity")
            if card_id is None or name is None or elixir is None or rarity is None:
                continue
            result.append({
                "id": str(card_id),
                "name": name,
                "elixir": int(elixir),
                "rarity": str(rarity).lower(),
                "type": c.get("type"),
                "icon_url": c.get("icon_url") or c.get("iconUrls", {}).get("medium") if isinstance(c.get("iconUrls"), dict) else c.get("icon_url"),
            })
        return result

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
                card_count=8,
                cards=self._extract_cards(deck.cards),
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
                cards=self._extract_cards(deck.cards),
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
                cards=self._extract_cards(deck.cards),
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

        ms = deck.matchup_stats or {}
        seasons = ms.get("seasons", {})

        if seasons:
            # Season-scoped structure (sync_top1000): use the latest season's data.
            latest_season = max(seasons.keys())
            season_data = seasons[latest_season]
            matchups_raw: dict[str, dict] = season_data.get("matchups", {})  # keys = sha1 deck_keys
            global_winrate: float = season_data.get("global_winrate") or 50.0
            meta_share: float = season_data.get("meta_share") or 0.0
            wins: int = season_data.get("wins", 0)
            losses: int = season_data.get("losses", 0)

            # Batch-load opponents by deck_key
            opp_decks_list = await self.deck_dal.get_by_deck_keys(list(matchups_raw.keys()))
            opponent_by_key: dict[str, Deck] = {}
            for opp in opp_decks_list:
                opp_key = (opp.matchup_stats or {}).get("deck_key")
                if opp_key:
                    opponent_by_key[opp_key] = opp

            matchups = self._extract_matchup_stats_by_key(matchups_raw, opponent_by_key)
        else:
            # Legacy structure (compute_deck_stats): matchups keyed by integer deck ID.
            matchups_raw = ms.get("matchups", {})
            global_winrate = ms.get("global_winrate") or 50.0
            meta_share = ms.get("meta_share") or 0.0
            wins = ms.get("wins", 0)
            losses = ms.get("losses", 0)

            opponent_decks: dict[int, Deck] = {}
            for key in matchups_raw:
                try:
                    opp_id = int(key)
                except ValueError:
                    continue
                opp = await self.deck_dal.get_by_id(opp_id)
                if opp:
                    opponent_decks[opp_id] = opp

            matchups = self._extract_matchup_stats(deck, opponent_decks)

        deck_response = self._deck_to_response(deck)

        return DeckStatsResponse(
            deck=deck_response,
            matchups=matchups,
            global_winrate=global_winrate,
            meta_share=meta_share,
            wins=wins,
            losses=losses,
        )

    def _extract_matchup_stats(self, deck: Deck, opponent_decks: dict[int, "Deck"]) -> list[MatchupStats]:
        """Extract and format matchup statistics from deck JSONB.

        Args:
            deck: Deck entity with matchup_stats
            opponent_decks: Pre-loaded opponent Deck entities keyed by ID

        Returns:
            List of matchup statistics sorted by sample_size descending
        """
        matchups_data = deck.matchup_stats.get("matchups", {})
        matchups = []

        for opponent_id_str, stats in matchups_data.items():
            try:
                opponent_id = int(opponent_id_str)
            except ValueError:
                continue

            opp = opponent_decks.get(opponent_id)
            if opp:
                opp_name = opp.name
                opp_archetype = opp.archetype
            else:
                opp_name = f"Deck #{opponent_id}"
                opp_archetype = "Unknown"

            matchups.append(
                MatchupStats(
                    opponent_deck_id=opponent_id,
                    opponent_deck_name=opp_name,
                    opponent_archetype=opp_archetype,
                    winrate=stats.get("winrate", 50.0),
                    wins=stats.get("wins", 0),
                    losses=stats.get("losses", 0),
                    sample_size=stats.get("sample_size", 0),
                    top_1000_winrate=stats.get("top_1000_winrate", 50.0),
                    last_updated=datetime.fromisoformat(
                        stats.get("last_updated", datetime.now(timezone.utc).isoformat())
                    ),
                )
            )

        matchups.sort(key=lambda m: m.sample_size, reverse=True)
        return matchups

    def _extract_matchup_stats_by_key(
        self,
        matchups_raw: dict[str, dict],
        opponent_by_key: dict[str, "Deck"],
    ) -> list[MatchupStats]:
        """Extract matchup stats from season-scoped data (deck_key-keyed)."""
        matchups = []
        for dk, stats in matchups_raw.items():
            opp = opponent_by_key.get(dk)
            if opp:
                opp_id = opp.id
                opp_name = opp.name
                opp_archetype = opp.archetype
            else:
                opp_id = 0
                opp_name = f"Deck {dk[:8]}…"
                opp_archetype = "Unknown"

            matchups.append(
                MatchupStats(
                    opponent_deck_id=opp_id,
                    opponent_deck_name=opp_name,
                    opponent_archetype=opp_archetype,
                    winrate=stats.get("winrate", 50.0),
                    wins=stats.get("wins", 0),
                    losses=stats.get("losses", 0),
                    sample_size=stats.get("sample_size", 0),
                    top_1000_winrate=stats.get("winrate", 50.0),
                    last_updated=datetime.fromisoformat(
                        stats.get("last_updated", datetime.now(timezone.utc).isoformat())
                    ),
                )
            )

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
        return DeckResponse(
            id=deck.id,
            name=deck.name,
            archetype=deck.archetype,
            cards=self._extract_cards(deck.cards),
            avg_elixir=deck.avg_elixir,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )
