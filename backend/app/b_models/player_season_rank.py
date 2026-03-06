"""ORM Model for player ranks per season.

Stores the leaderboard snapshot of a player for a given season.
A player can have at most one rank entry per season (unique constraint
on player_id + season_id).
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.b_models.player import Player
    from app.b_models.season import Season


class PlayerSeasonRank(Base):
    """Leaderboard rank of a player during a specific season."""

    __tablename__ = "player_season_ranks"

    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_player_season"),
    )

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Foreign keys
    # -------------------------------------------------------------------------
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------------------------------
    # Rank data
    # -------------------------------------------------------------------------
    league_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    league_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trophies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # -------------------------------------------------------------------------
    # Housekeeping  (when was this snapshot taken)
    # -------------------------------------------------------------------------
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    player: Mapped["Player"] = relationship("Player", back_populates="season_ranks")
    season: Mapped["Season"] = relationship("Season", back_populates="player_ranks")

    def __repr__(self) -> str:
        return (
            f"<PlayerSeasonRank player_id={self.player_id} "
            f"season_id={self.season_id} rank={self.league_rank}>"
        )
