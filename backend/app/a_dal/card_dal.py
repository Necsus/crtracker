"""Data Access Layer for Card entities.

Handles all database read operations for Clash Royale cards.
"""

from collections.abc import Sequence

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.base_dal import BaseDAL
from app.b_models.card import Card


class CardDAL(BaseDAL[Card]):
    """DAL for Card read operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Card)

    async def list_all(
        self,
        rarity: str | None = None,
        card_type: str | None = None,
        offset: int = 0,
        limit: int = 200,
    ) -> Sequence[Card]:
        """Return all cards, optionally filtered by rarity and/or type.

        Args:
            rarity: Title-case rarity to filter by (e.g. "Legendary")
            card_type: Title-case type to filter by (e.g. "Troop")
            offset: Pagination offset
            limit: Maximum rows to return

        Returns:
            Sequence of Card ORM instances
        """
        stmt = select(Card).order_by(Card.name)
        if rarity:
            stmt = stmt.where(Card.rarity == rarity.capitalize())
        if card_type:
            stmt = stmt.where(Card.card_type == card_type.capitalize())
        stmt = stmt.offset(offset).limit(limit)
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search(
        self,
        query: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Card]:
        """Search cards by name (case-insensitive substring).

        Args:
            query: Search term
            offset: Pagination offset
            limit: Maximum rows to return

        Returns:
            Sequence of matching Card ORM instances
        """
        stmt = (
            select(Card)
            .where(Card.name.ilike(f"%{query}%"))
            .order_by(Card.name)
            .offset(offset)
            .limit(limit)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()
