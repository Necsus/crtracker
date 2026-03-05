"""ORM Model for Clash Royale cards.

Mirrors the Clash Royale API /cards response.
Updated via the sync_cards script on each game patch.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Card(Base):
    """Represents a Clash Royale card.

    Fields are sourced from the official CR API GET /cards endpoint.
    The full raw API payload is also stored in raw_data for forward compatibility.
    """

    __tablename__ = "cards"

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # CR API identifiers
    # -------------------------------------------------------------------------
    # Numeric ID returned by the CR API (e.g. 26000000 for Knight)
    card_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # -------------------------------------------------------------------------
    # Gameplay attributes
    # -------------------------------------------------------------------------
    # "Common", "Rare", "Epic", "Legendary", "Champion"
    rarity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # "Troop", "Building", "Spell"
    card_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Elixir cost (0 for Mirror / free spells)
    elixir_cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Max level reachable (14 for Common, 11 for Rare, 8 for Epic, 5 for Legendary…)
    max_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Max evolution level – only set for cards that can be evolved
    max_evolution_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Deploy time in tenths of a second
    deploy_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Movement speed: "Slow", "Medium", "Fast", "Very Fast"
    speed: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Which arena unlocks this card (1 = Training, 2 = Goblin Stadium, …)
    arena_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Official in-game description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Targets stored as JSON array, e.g. ["Ground"], ["Air", "Ground"]
    # -------------------------------------------------------------------------
    target: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Asset URLs
    # -------------------------------------------------------------------------
    icon_url_medium: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # -------------------------------------------------------------------------
    # Full raw payload from the CR API (for forward-compatibility)
    # -------------------------------------------------------------------------
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    # Set at first insert
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Set every time the row is updated by the sync script
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
