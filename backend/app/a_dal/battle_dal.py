"""DAL for battles — read-only queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.b_models.battle import Battle

# SQL fragment: count how many of a team's card names appear in the given name list.
# Used to match battles to a specific deck (all 8 card names must match).
_TEAM_MATCH_SQL = (
    "(SELECT COUNT(*) FROM jsonb_array_elements({col}::jsonb) c"
    " WHERE c->>'name' = ANY(:names)) = :cnt"
)


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

    async def list_battles_by_card_names(
        self,
        card_names: list[str],
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Battle]:
        """Return battles where either team used a deck matching all given card names."""
        stmt = (
            select(Battle)
            .where(
                or_(
                    text(_TEAM_MATCH_SQL.format(col="team1_cards")),
                    text(_TEAM_MATCH_SQL.format(col="team2_cards")),
                )
            )
            .order_by(Battle.battle_time.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt, {"names": card_names, "cnt": len(card_names)})
        return result.scalars().all()

    async def count_battles_by_card_names(self, card_names: list[str]) -> int:
        """Count battles where either team used a deck matching all given card names."""
        stmt = (
            select(func.count())
            .select_from(Battle)
            .where(
                or_(
                    text(_TEAM_MATCH_SQL.format(col="team1_cards")),
                    text(_TEAM_MATCH_SQL.format(col="team2_cards")),
                )
            )
        )
        result = await self.session.execute(stmt, {"names": card_names, "cnt": len(card_names)})
        return result.scalar_one()
