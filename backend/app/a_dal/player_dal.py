"""Player data access layer."""

from datetime import datetime, timezone

from sqlalchemy import asc, desc, func, nulls_last, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.b_models.player import Player


class PlayerDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        return tag.strip().upper().lstrip("#")

    async def get_by_tag(self, tag: str) -> Player | None:
        result = await self.session.execute(
            select(Player).where(Player.tag == self._normalize_tag(tag))
        )
        return result.scalar_one_or_none()

    async def search_by_name(self, query: str, limit: int = 10) -> list[Player]:
        result = await self.session.execute(
            select(Player)
            .where(Player.name.ilike(f"%{query}%"))
            .order_by(nulls_last(asc(Player.pol_rank)), desc(Player.trophies))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_tag_fragment(self, fragment: str, limit: int = 10) -> list[Player]:
        normalized = self._normalize_tag(fragment)
        result = await self.session.execute(
            select(Player)
            .where(Player.tag.ilike(f"%{normalized}%"))
            .order_by(nulls_last(asc(Player.pol_rank)), desc(Player.trophies))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_top(self, limit: int = 20, offset: int = 0) -> list[Player]:
        """Return top players ordered by PoL rank first, then trophies."""
        result = await self.session.execute(
            select(Player)
            .order_by(nulls_last(asc(Player.pol_rank)), desc(Player.trophies))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(Player.id)))
        return result.scalar_one()

    async def upsert(self, data: dict) -> Player:
        """Insert or update a player by tag (upsert on unique tag constraint)."""
        tag = self._normalize_tag(data.get("tag", ""))
        data = {**data, "tag": tag}

        # Fields to update on conflict (everything except immutable identity cols)
        update_set = {k: v for k, v in data.items() if k not in ("tag", "created_at")}
        update_set["last_synced_at"] = datetime.now(timezone.utc)

        stmt = (
            pg_insert(Player)
            .values(**data)
            .on_conflict_do_update(
                constraint="uq_players_tag",
                set_=update_set,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_tag(tag)  # type: ignore[return-value]
