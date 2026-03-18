"""ORM Model for per-season deck competitive status.

This is the temporal/competitive dimension of deck classification, intentionally
separated from the permanent structural Archetype model.

One row per (deck × season). Populated by a periodic background job that
aggregates battle logs.

Status ladder (from most to least prominent):
  DOMINANT      High usage AND high winrate — the "tier 1 meta" decks.
  VIABLE        Present in the meta with decent winrate — "tier 2".
  ANTI_META     Low usage but statistically strong against DOMINANT decks.
  OFF_META      Low usage, no notable anti-meta correlation.
  UNCLASSIFIED  Not enough sample size or deck not yet analysed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeckMetaStatus(Base):
    """Competitive meta status for a deck in a given season."""

    __tablename__ = "deck_meta_statuses"

    __table_args__ = (
        UniqueConstraint("deck_id", "season_id", name="uq_deck_season_status"),
    )

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # References
    # -------------------------------------------------------------------------
    deck_id: Mapped[int] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------
    # DOMINANT | VIABLE | ANTI_META | OFF_META | UNCLASSIFIED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="UNCLASSIFIED"
    )

    # -------------------------------------------------------------------------
    # Stats snapshot (at computation time)
    # -------------------------------------------------------------------------
    # Percentage of top-ladder battles in which this deck appeared (0-100)
    usage_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Overall winrate this season (0-100)
    winrate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Number of battles used to compute these stats
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<DeckMetaStatus(deck_id={self.deck_id}, season_id={self.season_id}"
            f", status='{self.status}', winrate={self.winrate})>"
        )
