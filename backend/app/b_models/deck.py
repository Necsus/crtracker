"""ORM Models for decks and matchups.

Uses JSONB fields extensively to store complex data structures
without excessive table relationships.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Deck(Base):
    """Represents a Clash Royale deck.

    Stores deck metadata and the 8 cards in a JSONB field.
    Matchup statistics are also stored as JSONB for flexibility.
    """

    __tablename__ = "decks"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Deck metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    archetype: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Cards stored as JSONB array of card objects
    # Example: [{"id": "golem", "name": "Golem", "elixir": 8, "rarity": "epic", ...}, ...]
    cards: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Computed values stored for performance
    avg_elixir: Mapped[float] = mapped_column(nullable=False)

    # Source information
    player_tag: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, index=True
    )

    # Matchup statistics stored as JSONB
    # Structure: {
    #   "global_winrate": 52.5,
    #   "meta_share": 15.3,
    #   "sample_size": 12450,
    #   "matchups": {
    #     "42": {  # opponent_deck_id
    #       "winrate": 58.2,
    #       "top_1000_winrate": 61.5,
    #       "sample_size": 3420,
    #       "last_updated": "2025-01-15T10:30:00Z"
    #     },
    #     ...
    #   }
    # }
    matchup_stats: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Oracle advice cache stored as JSONB
    # Structure: {
    #   "42": {  # opponent_deck_id
    #     "advice": [...],
    #     "generated_at": "2025-01-15T10:30:00Z",
    #     "winrate_prediction": 55.0
    #   }
    # }
    oracle_cache: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Deck(id={self.id}, name='{self.name}', archetype='{self.archetype}')>"

    @property
    def card_count(self) -> int:
        """Return the number of cards in the deck."""
        return len(self.cards.get("cards", []))

    @property
    def global_winrate(self) -> float | None:
        """Return the global winrate from matchup stats."""
        return self.matchup_stats.get("global_winrate")

    @property
    def meta_share(self) -> float | None:
        """Return the meta share percentage."""
        return self.matchup_stats.get("meta_share")
