"""Data Access Layer for Archetype and DeckMetaStatus entities."""

from collections.abc import Sequence

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.a_dal.base_dal import BaseDAL
from app.b_models.archetype import Archetype
from app.b_models.deck_meta_status import DeckMetaStatus


class ArchetypeDAL(BaseDAL[Archetype]):
    """DAL for Archetype operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Archetype)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_all_with_variants(self) -> Sequence[Archetype]:
        """Return all archetypes, with their 'variants' relationship pre-loaded."""
        stmt = (
            select(Archetype)
            .options(selectinload(Archetype.variants))
            .order_by(Archetype.name)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_root_archetypes(self) -> Sequence[Archetype]:
        """Return only root archetypes (not variants of anything)."""
        stmt = (
            select(Archetype)
            .where(Archetype.variant_of_id.is_(None))
            .options(selectinload(Archetype.variants))
            .order_by(Archetype.name)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_timeless(self) -> Sequence[Archetype]:
        """Return all 'Indemodable' archetypes."""
        stmt = (
            select(Archetype)
            .where(Archetype.is_timeless.is_(True))
            .order_by(Archetype.name)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Archetype | None:
        """Exact name lookup (case-insensitive)."""
        stmt = select(Archetype).where(Archetype.name.ilike(name))
        result: Result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_variants_of(self, parent_id: int) -> Sequence[Archetype]:
        """Return all immediate variant children of an archetype."""
        stmt = (
            select(Archetype)
            .where(Archetype.variant_of_id == parent_id)
            .order_by(Archetype.name)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_candidates_for_fingerprint(self) -> Sequence[Archetype]:
        """Return all archetypes ordered by core_cards length DESC.

        Longer core_cards lists are more specific; during fingerprinting we
        try the most specific archetypes first to avoid false matches on parent
        archetypes that share only the win condition.
        """
        stmt = select(Archetype).order_by(Archetype.name)
        result: Result = await self.session.execute(stmt)
        archetypes = list(result.scalars().all())
        # Sort in Python: most specific (longest core_cards) first
        archetypes.sort(key=lambda a: len(a.core_cards or []), reverse=True)
        return archetypes


class DeckMetaStatusDAL(BaseDAL[DeckMetaStatus]):
    """DAL for DeckMetaStatus operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DeckMetaStatus)

    async def get_for_deck(self, deck_id: int) -> Sequence[DeckMetaStatus]:
        """Return all meta statuses for a deck, ordered by season_id desc."""
        stmt = (
            select(DeckMetaStatus)
            .where(DeckMetaStatus.deck_id == deck_id)
            .order_by(DeckMetaStatus.season_id.desc())
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_current(self, deck_id: int, season_id: int) -> DeckMetaStatus | None:
        """Return the meta status for a specific (deck, season) pair."""
        stmt = select(DeckMetaStatus).where(
            DeckMetaStatus.deck_id == deck_id,
            DeckMetaStatus.season_id == season_id,
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_status(
        self, status: str, season_id: int
    ) -> Sequence[DeckMetaStatus]:
        """Return all deck statuses matching a given status in a season."""
        stmt = (
            select(DeckMetaStatus)
            .where(
                DeckMetaStatus.status == status,
                DeckMetaStatus.season_id == season_id,
            )
            .order_by(DeckMetaStatus.usage_rate.desc().nulls_last())
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert(
        self,
        deck_id: int,
        season_id: int,
        status: str,
        usage_rate: float | None,
        winrate: float | None,
        sample_size: int | None,
    ) -> DeckMetaStatus:
        """Insert or update a DeckMetaStatus row."""
        existing = await self.get_current(deck_id, season_id)
        if existing:
            existing.status = status
            existing.usage_rate = usage_rate
            existing.winrate = winrate
            existing.sample_size = sample_size
            await self.session.flush()
            return existing

        entry = DeckMetaStatus(
            deck_id=deck_id,
            season_id=season_id,
            status=status,
            usage_rate=usage_rate,
            winrate=winrate,
            sample_size=sample_size,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
