"""Battle ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Player this battle belongs to
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Unique key: "{player_tag}_{battle_time_raw}" to deduplicate on upsert
    battle_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    battle_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    battle_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    game_mode_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    arena_name: Mapped[str | None] = mapped_column(String(80), nullable=True)

    result: Mapped[str] = mapped_column(String(10), nullable=False)  # 'win' | 'loss' | 'draw'
    trophy_change: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player_crowns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    opponent_tag: Mapped[str | None] = mapped_column(String(20), nullable=True)
    opponent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    opponent_crowns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opponent_trophies: Mapped[int | None] = mapped_column(Integer, nullable=True)

    player_cards: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    opponent_cards: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
