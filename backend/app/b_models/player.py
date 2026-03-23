"""Player ORM model — maps to the `players` table."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Player(Base):
    """Clash Royale player.

    Indexed columns cover all common filter/sort operations.
    Everything else (deck, badges, achievements, raw response) lives in JSONB.
    """

    __tablename__ = "players"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    tag: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ------------------------------------------------------------------
    # Progression
    # ------------------------------------------------------------------
    exp_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exp_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_exp_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    star_points: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Trophy Road
    # ------------------------------------------------------------------
    trophies: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    best_trophies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    legacy_trophy_road_high_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Battle stats
    # ------------------------------------------------------------------
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    battle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    three_crown_wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ------------------------------------------------------------------
    # Challenge & tournament stats
    # ------------------------------------------------------------------
    challenge_cards_won: Mapped[int | None] = mapped_column(Integer, nullable=True)
    challenge_max_wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tournament_cards_won: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tournament_battle_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Clan & social stats
    # ------------------------------------------------------------------
    war_day_wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clan_cards_collected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    donations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    donations_received: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_donations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clan_tag: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    clan_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    clan_badge_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ------------------------------------------------------------------
    # Arena
    # ------------------------------------------------------------------
    arena_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arena_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ------------------------------------------------------------------
    # Path of Legends (ranked mode)
    # ------------------------------------------------------------------
    pol_league_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    pol_trophies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pol_rank: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # ------------------------------------------------------------------
    # JSONB blobs (rich data, not directly filterable)
    # ------------------------------------------------------------------
    current_deck: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """List of 8 card objects: {name, id, level, maxLevel, starLevel?, evolutionLevel?, iconUrls}"""

    current_favourite_card: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """Single card object."""

    league_statistics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """currentSeason / previousSeason / bestSeason with rank + trophies."""

    badges: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Array of badge objects: {name, level, maxLevel, progress, target, iconUrls}."""

    achievements: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Array of achievement objects: {name, stars, value, target, info, completionInfo}."""

    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """Full API response, kept for forward-compatibility."""

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
