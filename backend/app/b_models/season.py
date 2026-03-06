"""ORM Model for Clash Royale seasons.

One season per month, but start/end timestamps are not necessarily
at midnight – the CR API decides exact cutoffs.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.b_models.player_season_rank import PlayerSeasonRank


class Season(Base):
    """A Clash Royale competitive season (≈ one per month)."""

    __tablename__ = "seasons"

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Human-readable label  (e.g. '2026-03')
    # -------------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)

    # -------------------------------------------------------------------------
    # Exact boundaries (timezone-aware).
    # end_at is NULL while the season is still active.
    # -------------------------------------------------------------------------
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -------------------------------------------------------------------------
    # Housekeeping
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    player_ranks: Mapped[list["PlayerSeasonRank"]] = relationship(
        "PlayerSeasonRank",
        back_populates="season",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Season id={self.id} name={self.name!r}>"
