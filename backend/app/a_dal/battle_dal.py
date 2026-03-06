"""DAL for battles — read-only queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.b_models.battle import Battle


class BattleDal:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_battles(
        self,
        battle_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Battle]:
        stmt = select(Battle).order_by(Battle.battle_time.desc())
        if battle_type:
            stmt = stmt.where(Battle.battle_type == battle_type)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_battles(self, battle_type: str | None = None) -> int:
        stmt = select(func.count()).select_from(Battle)
        if battle_type:
            stmt = stmt.where(Battle.battle_type == battle_type)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_battle_types(self) -> list[str]:
        stmt = (
            select(Battle.battle_type)
            .where(Battle.battle_type.isnot(None))
            .distinct()
            .order_by(Battle.battle_type)
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]
