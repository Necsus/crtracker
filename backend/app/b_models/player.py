"""ORM Model for Clash Royale players.

Populated by the sync_players script.  Each row represents one player
from the Path of Legend global leaderboard, with their profile data and
current deck.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Player(Base):
    """A Clash Royale player from the Path of Legend leaderboard."""

    __tablename__ = "players"

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Identity  (tag stored WITHOUT the leading '#')
    # -------------------------------------------------------------------------
    tag: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # -------------------------------------------------------------------------
    # Profile stats
    # -------------------------------------------------------------------------
    trophies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    best_trophies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exp_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wins: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    losses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    battle_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # -------------------------------------------------------------------------
    # Path of Legend leaderboard position
    # -------------------------------------------------------------------------
    league_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Global rank (1 = #1 on the leaderboard)
    league_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    # Season in which the rank was captured  (e.g. '2026-03')
    season: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # -------------------------------------------------------------------------
    # Current deck – JSON array of card objects as returned by the CR API
    # -------------------------------------------------------------------------
    current_deck: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Raw full profile payload from /v1/players/{tag}
    # -------------------------------------------------------------------------
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Housekeeping
    # -------------------------------------------------------------------------
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
