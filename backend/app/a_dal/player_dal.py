"""Data Access Layer for Player operations.

Queries the `players` table populated by the sync_players script.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.b_models.player import Player


class PlayerDAL:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Single player lookup
    # ------------------------------------------------------------------

    async def get_by_tag(self, tag: str) -> Player | None:
        """Return a player by battle tag (with or without leading '#')."""
        clean = tag.lstrip("#").upper()
        stmt = select(Player).where(Player.tag == clean)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_players(self, query: str, limit: int = 20) -> Sequence[Player]:
        """Search players by name (case-insensitive) or by tag (exact, strips '#')."""
        clean_tag = query.lstrip("#").upper()
        name_pattern = f"%{query}%"
        stmt = (
            select(Player)
            .where(
                or_(
                    Player.name.ilike(name_pattern),
                    Player.tag == clean_tag,
                )
            )
            .order_by(Player.league_rank.asc().nulls_last())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ------------------------------------------------------------------
    # List / paginate
    # ------------------------------------------------------------------

    async def list_players(
        self,
        season: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Player]:
        stmt = select(Player).order_by(Player.league_rank.asc().nulls_last())
        if season:
            stmt = stmt.where(Player.season == season)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_players(self, season: str | None = None) -> int:
        stmt = select(func.count()).select_from(Player)
        if season:
            stmt = stmt.where(Player.season == season)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Available seasons
    # ------------------------------------------------------------------

    async def list_seasons(self) -> list[str]:
        stmt = (
            select(Player.season)
            .where(Player.season.isnot(None))
            .distinct()
            .order_by(Player.season.desc())
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    # ------------------------------------------------------------------
    # Upsert (used when fetching live from CR API)
    # ------------------------------------------------------------------

    async def upsert_from_api(self, data: dict) -> Player:
        """Insert or update a player row from a raw CR API response dict.

        The player is identified by ``tag`` (without leading ``#``).
        All provided fields are updated on conflict.
        Returns the refreshed ORM instance.
        """
        tag = data.get("tag", "").lstrip("#").upper()
        values = {
            "tag": tag,
            "name": data.get("name"),
            "trophies": data.get("trophies"),
            "best_trophies": data.get("bestTrophies"),
            "exp_level": data.get("expLevel"),
            "wins": data.get("wins"),
            "losses": data.get("losses"),
            "battle_count": data.get("battleCount"),
            "current_deck": data.get("currentDeck"),
        }
        stmt = (
            pg_insert(Player)
            .values(**values)
            .on_conflict_do_update(index_elements=["tag"], set_=values)
            .returning(Player)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Kept for backward compat — real API call happens in the sync script
    # ------------------------------------------------------------------

    async def get_player_profile(self, player_tag: str) -> "Player | None":
        """Alias for get_by_tag — kept for backward compatibility."""
        return await self.get_by_tag(player_tag)
