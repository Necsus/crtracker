"""Battle data access layer."""

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.b_models.battle import Battle


class BattleDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_many(self, battles: list[dict]) -> None:
        """Insert battles, ignoring duplicates by battle_key."""
        if not battles:
            return
        stmt = (
            pg_insert(Battle)
            .values(battles)
            .on_conflict_do_nothing(constraint="uq_battles_battle_key")
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_by_player_tag(self, player_tag: str, limit: int = 25) -> list[Battle]:
        result = await self.session.execute(
            select(Battle)
            .where(Battle.player_tag == player_tag.upper().lstrip("#"))
            .order_by(desc(Battle.battle_time))
            .limit(limit)
        )
        return list(result.scalars().all())
