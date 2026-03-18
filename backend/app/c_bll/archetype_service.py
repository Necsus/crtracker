"""Business Logic Layer for Archetype management and deck fingerprinting.

Responsibilities:
  1. CRUD on the curated archetypes table.
  2. Fingerprint a deck (list of card slugs) → best matching Archetype.
  3. Classify a deck's meta_status for a season (intended to be called by a
     background compute job, not on every request).

Fingerprinting algorithm
------------------------
Given a deck (8 card slugs):
  1. Load all archetypes, sorted by core_cards length DESC (most specific first).
  2. For each archetype, check if ALL its core_cards are present in the deck.
  3. The first (most specific) archetype that matches wins.
  4. If no archetype matches, return None (deck will stay UNCLASSIFIED).

This "most-specific-first" approach means:
  - Hog 2.6  (core: hog-rider, ice-golem, ice-spirit, skeletons) wins over
  - Hog Cycle (core: hog-rider)
  when the deck contains all four of those cards.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.archetype_dal import ArchetypeDAL, DeckMetaStatusDAL
from app.b_models.archetype import Archetype
from app.b_models.deck import Deck
from app.schemas import (
    ArchetypeCreate,
    ArchetypeListItem,
    ArchetypeResponse,
    ArchetypeWithVariants,
    DeckMetaStatusResponse,
    DeckMetaStatusUpdate,
)


class ArchetypeService:
    """Service for archetype management and deck fingerprinting."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.archetype_dal = ArchetypeDAL(session)
        self.meta_status_dal = DeckMetaStatusDAL(session)

    # ------------------------------------------------------------------
    # Archetype CRUD
    # ------------------------------------------------------------------

    async def list_archetypes(self) -> list[ArchetypeListItem]:
        archetypes = await self.archetype_dal.get_all_with_variants()
        return [self._to_list_item(a) for a in archetypes]

    async def list_timeless(self) -> list[ArchetypeListItem]:
        archetypes = await self.archetype_dal.get_timeless()
        return [self._to_list_item(a) for a in archetypes]

    async def get_archetype(self, archetype_id: int) -> ArchetypeWithVariants | None:
        archetype = await self.archetype_dal.get_by_id(archetype_id)
        if not archetype:
            return None
        variants = await self.archetype_dal.get_variants_of(archetype_id)
        return ArchetypeWithVariants(
            **self._to_response(archetype).model_dump(),
            variants=[self._to_list_item(v) for v in variants],
        )

    async def get_root_archetypes(self) -> list[ArchetypeWithVariants]:
        roots = await self.archetype_dal.get_root_archetypes()
        result = []
        for root in roots:
            variants = await self.archetype_dal.get_variants_of(root.id)
            result.append(
                ArchetypeWithVariants(
                    **self._to_response(root).model_dump(),
                    variants=[self._to_list_item(v) for v in variants],
                )
            )
        return result

    async def create_archetype(self, payload: ArchetypeCreate) -> ArchetypeResponse:
        archetype = Archetype(
            name=payload.name,
            win_condition=payload.win_condition,
            play_style=payload.play_style,
            is_timeless=payload.is_timeless,
            variant_of_id=payload.variant_of_id,
            core_cards=payload.core_cards,
            description=payload.description,
        )
        self.session.add(archetype)
        await self.session.flush()
        await self.session.refresh(archetype)
        return self._to_response(archetype)

    async def update_archetype(
        self, archetype_id: int, payload: ArchetypeCreate
    ) -> ArchetypeResponse | None:
        archetype = await self.archetype_dal.get_by_id(archetype_id)
        if not archetype:
            return None
        archetype.name = payload.name
        archetype.win_condition = payload.win_condition
        archetype.play_style = payload.play_style
        archetype.is_timeless = payload.is_timeless
        archetype.variant_of_id = payload.variant_of_id
        archetype.core_cards = payload.core_cards
        archetype.description = payload.description
        await self.session.flush()
        return self._to_response(archetype)

    async def delete_archetype(self, archetype_id: int) -> bool:
        archetype = await self.archetype_dal.get_by_id(archetype_id)
        if not archetype:
            return False
        await self.session.delete(archetype)
        await self.session.flush()
        return True

    # ------------------------------------------------------------------
    # Fingerprinting
    # ------------------------------------------------------------------

    @staticmethod
    def compute_deck_key(card_ids: list[str]) -> str:
        """Compute the SHA-1 fingerprint for a list of card ID slugs.

        The list is sorted before hashing so that card order does not matter.
        Returns a 40-character lowercase hex string.
        """
        normalised = sorted(str(cid).lower().strip() for cid in card_ids)
        raw = ",".join(normalised)
        return hashlib.sha1(raw.encode()).hexdigest()

    async def fingerprint_deck(self, card_ids: list[str]) -> Archetype | None:
        """Return the best matching Archetype for a deck, or None.

        Most-specific-first: an archetype with more core_cards wins over
        a parent archetype that only requires the win condition card.
        """
        candidates = await self.archetype_dal.get_candidates_for_fingerprint()
        card_set = {str(cid).lower().strip() for cid in card_ids}

        for archetype in candidates:
            required = {c.lower().strip() for c in (archetype.core_cards or [])}
            if not required:
                continue  # never match an archetype with empty core_cards
            if required.issubset(card_set):
                return archetype

        return None

    async def classify_deck(self, deck: Deck) -> Archetype | None:
        """Fingerprint a Deck ORM object and persist archetype_id + deck_key.

        Returns the matched Archetype or None if no match.
        """
        cards_raw = deck.cards
        if isinstance(cards_raw, dict):
            cards_raw = cards_raw.get("cards", [])
        if not isinstance(cards_raw, list):
            return None

        card_ids = [str(c.get("id", "")) for c in cards_raw if isinstance(c, dict)]
        card_ids = [cid for cid in card_ids if cid]

        # Always update deck_key
        if card_ids:
            deck.deck_key = self.compute_deck_key(card_ids)

        matched = await self.fingerprint_deck(card_ids)
        if matched:
            deck.archetype_id = matched.id

        await self.session.flush()
        return matched

    async def classify_all_unclassified(self) -> dict:
        """Run fingerprinting on every deck that has no archetype_id yet.

        Returns a summary dict with counts of matched, unmatched, and errors.
        Intended to be called as a one-off admin operation or background job.
        """
        from sqlalchemy import select
        from app.b_models.deck import Deck as DeckModel

        stmt = select(DeckModel).where(DeckModel.archetype_id.is_(None))
        result = await self.session.execute(stmt)
        decks = result.scalars().all()

        matched = 0
        unmatched = 0
        errors = 0

        for deck in decks:
            try:
                arch = await self.classify_deck(deck)
                if arch:
                    matched += 1
                else:
                    unmatched += 1
            except Exception:
                errors += 1

        await self.session.commit()
        return {"matched": matched, "unmatched": unmatched, "errors": errors}

    # ------------------------------------------------------------------
    # Meta status management
    # ------------------------------------------------------------------

    async def upsert_meta_status(
        self, payload: DeckMetaStatusUpdate
    ) -> DeckMetaStatusResponse:
        entry = await self.meta_status_dal.upsert(
            deck_id=payload.deck_id,
            season_id=payload.season_id,
            status=payload.status,
            usage_rate=payload.usage_rate,
            winrate=payload.winrate,
            sample_size=payload.sample_size,
        )
        return DeckMetaStatusResponse(
            id=entry.id,
            deck_id=entry.deck_id,
            season_id=entry.season_id,
            status=entry.status,  # type: ignore[arg-type]
            usage_rate=entry.usage_rate,
            winrate=entry.winrate,
            sample_size=entry.sample_size,
            computed_at=entry.computed_at,
        )

    async def get_deck_meta_history(
        self, deck_id: int
    ) -> list[DeckMetaStatusResponse]:
        statuses = await self.meta_status_dal.get_for_deck(deck_id)
        return [
            DeckMetaStatusResponse(
                id=s.id,
                deck_id=s.deck_id,
                season_id=s.season_id,
                status=s.status,  # type: ignore[arg-type]
                usage_rate=s.usage_rate,
                winrate=s.winrate,
                sample_size=s.sample_size,
                computed_at=s.computed_at,
            )
            for s in statuses
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_response(self, a: Archetype) -> ArchetypeResponse:
        return ArchetypeResponse(
            id=a.id,
            name=a.name,
            win_condition=a.win_condition,
            play_style=a.play_style,  # type: ignore[arg-type]
            is_timeless=a.is_timeless,
            variant_of_id=a.variant_of_id,
            variant_of_name=(
                a.parent_archetype.name if a.parent_archetype else None
            ),
            core_cards=a.core_cards or [],
            description=a.description,
            created_at=a.created_at,
        )

    def _to_list_item(self, a: Archetype) -> ArchetypeListItem:
        return ArchetypeListItem(
            id=a.id,
            name=a.name,
            win_condition=a.win_condition,
            play_style=a.play_style,  # type: ignore[arg-type]
            is_timeless=a.is_timeless,
            variant_of_id=a.variant_of_id,
            core_cards=a.core_cards or [],
        )
