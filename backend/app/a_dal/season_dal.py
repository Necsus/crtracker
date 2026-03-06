"""Data Access Layer for Season and PlayerSeasonRank operations."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.b_models.player_season_rank import PlayerSeasonRank
from app.b_models.season import Season


class SeasonDAL:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Season CRUD
    # ------------------------------------------------------------------

    async def get_by_id(self, season_id: int) -> Season | None:
        stmt = select(Season).where(Season.id == season_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Season | None:
        """Return a season by its label (e.g. '2026-03')."""
        stmt = select(Season).where(Season.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active(self) -> Season | None:
        """Return the season whose end_at is NULL (currently active)."""
        stmt = select(Season).where(Season.end_at.is_(None)).order_by(Season.start_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_seasons(self, offset: int = 0, limit: int = 50) -> Sequence[Season]:
        stmt = select(Season).order_by(Season.start_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        name: str,
        start_at: datetime,
        end_at: datetime | None = None,
    ) -> Season:
        season = Season(name=name, start_at=start_at, end_at=end_at)
        self.session.add(season)
        await self.session.flush()
        return season

    async def close_season(self, season_id: int, end_at: datetime) -> Season | None:
        """Set the end_at timestamp to mark a season as closed."""
        season = await self.get_by_id(season_id)
        if season is None:
            return None
        season.end_at = end_at
        await self.session.flush()
        return season

    # ------------------------------------------------------------------
    # PlayerSeasonRank operations
    # ------------------------------------------------------------------

    async def get_rank(self, player_id: int, season_id: int) -> PlayerSeasonRank | None:
        stmt = select(PlayerSeasonRank).where(
            PlayerSeasonRank.player_id == player_id,
            PlayerSeasonRank.season_id == season_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_rank(
        self,
        player_id: int,
        season_id: int,
        league_rank: int | None,
        league_number: int | None = None,
        trophies: int | None = None,
    ) -> PlayerSeasonRank:
        """Insert or update a player rank entry for the given season."""
        existing = await self.get_rank(player_id, season_id)
        if existing is not None:
            existing.league_rank = league_rank
            existing.league_number = league_number
            existing.trophies = trophies
            existing.synced_at = datetime.now().astimezone()
            await self.session.flush()
            return existing

        rank = PlayerSeasonRank(
            player_id=player_id,
            season_id=season_id,
            league_rank=league_rank,
            league_number=league_number,
            trophies=trophies,
        )
        self.session.add(rank)
        await self.session.flush()
        return rank

    async def list_ranks_for_season(
        self,
        season_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[PlayerSeasonRank]:
        """Return all player ranks for a season, ordered by rank asc."""
        stmt = (
            select(PlayerSeasonRank)
            .where(PlayerSeasonRank.season_id == season_id)
            .order_by(PlayerSeasonRank.league_rank.asc().nulls_last())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_ranks_for_player(
        self,
        player_id: int,
    ) -> Sequence[PlayerSeasonRank]:
        """Return the full rank history for a player, most recent first."""
        stmt = (
            select(PlayerSeasonRank)
            .where(PlayerSeasonRank.player_id == player_id)
            .join(PlayerSeasonRank.season)
            .order_by(Season.start_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
