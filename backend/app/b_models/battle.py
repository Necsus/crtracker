"""ORM Model for Clash Royale battles.

Populated by the sync_battles script.  Each row represents one PvP match,
normalised so the same game seen from both players' battle logs maps to a
single row (dedup via battle_key).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Battle(Base):
    """A single Clash Royale match between two players."""

    __tablename__ = "battles"

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Deduplication key
    # Format: "{battleTime}_{min(tag1,tag2)}_{max(tag1,tag2)}"
    # Guarantees the same game seen from both players' logs maps to one row.
    # -------------------------------------------------------------------------
    battle_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)

    # -------------------------------------------------------------------------
    # Timing & mode
    # -------------------------------------------------------------------------
    battle_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # "PvP", "ClanWar", "Tournament", …
    battle_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)

    game_mode_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    game_mode_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    arena_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    arena_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    # -------------------------------------------------------------------------
    # Team 1  (normalised: alphabetically lower player tag)
    # -------------------------------------------------------------------------
    team1_tag: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    team1_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team1_crowns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team1_starting_trophies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team1_trophy_change: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # JSON array: [{"id": 26000000, "name": "Knight", "level": 14, ...}, …]
    team1_cards: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Team 2  (normalised: alphabetically greater player tag)
    # -------------------------------------------------------------------------
    team2_tag: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    team2_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team2_crowns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team2_starting_trophies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team2_trophy_change: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team2_cards: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Result
    # -------------------------------------------------------------------------
    # Winner player tag (None = draw)
    winner_tag: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)

    # -------------------------------------------------------------------------
    # Full raw CR API battle object kept for future use / reprocessing
    # -------------------------------------------------------------------------
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # -------------------------------------------------------------------------
    # Book-keeping
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Battle(id={self.id}, "
            f"{self.team1_tag} vs {self.team2_tag}, "
            f"{self.battle_time.date()})>"
        )
