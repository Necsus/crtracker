"""API routes for archetype management and deck fingerprinting.

Endpoints:
  GET  /api/v1/archetypes                  — list all archetypes
  GET  /api/v1/archetypes/timeless         — list 'Indemodable' archetypes
  GET  /api/v1/archetypes/tree             — root archetypes with their variants
  GET  /api/v1/archetypes/{id}             — single archetype with variants
  POST /api/v1/archetypes                  — create a curated archetype
  PUT  /api/v1/archetypes/{id}             — update an archetype
  DELETE /api/v1/archetypes/{id}           — delete an archetype

  POST /api/v1/archetypes/classify/all     — fingerprint all unclassified decks
  POST /api/v1/archetypes/classify/{deck_id} — fingerprint a single deck

  GET  /api/v1/archetypes/meta/{deck_id}   — meta history for a deck
  POST /api/v1/archetypes/meta             — upsert meta status (called by compute job)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.c_bll.archetype_service import ArchetypeService
from app.database import get_db
from app.schemas import (
    ArchetypeCreate,
    ArchetypeListItem,
    ArchetypeResponse,
    ArchetypeWithVariants,
    DeckMetaStatusResponse,
    DeckMetaStatusUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["archetypes"])


# --------------------------------------------------------------------------
# Dependency
# --------------------------------------------------------------------------


async def get_archetype_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchetypeService:
    return ArchetypeService(db)


# --------------------------------------------------------------------------
# Read endpoints
# --------------------------------------------------------------------------


@router.get(
    "/archetypes",
    response_model=list[ArchetypeListItem],
    summary="List all archetypes",
)
async def list_archetypes(
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> list[ArchetypeListItem]:
    return await service.list_archetypes()


@router.get(
    "/archetypes/timeless",
    response_model=list[ArchetypeListItem],
    summary="List 'Indemodable' archetypes",
)
async def list_timeless(
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> list[ArchetypeListItem]:
    return await service.list_timeless()


@router.get(
    "/archetypes/tree",
    response_model=list[ArchetypeWithVariants],
    summary="Root archetypes with their variant children",
)
async def get_archetype_tree(
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> list[ArchetypeWithVariants]:
    return await service.get_root_archetypes()


@router.get(
    "/archetypes/{archetype_id}",
    response_model=ArchetypeWithVariants,
    summary="Get a single archetype with its variants",
)
async def get_archetype(
    archetype_id: int,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> ArchetypeWithVariants:
    archetype = await service.get_archetype(archetype_id)
    if not archetype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archetype {archetype_id} not found",
        )
    return archetype


# --------------------------------------------------------------------------
# Write endpoints
# --------------------------------------------------------------------------


@router.post(
    "/archetypes",
    response_model=ArchetypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a curated archetype",
)
async def create_archetype(
    payload: ArchetypeCreate,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> ArchetypeResponse:
    return await service.create_archetype(payload)


@router.put(
    "/archetypes/{archetype_id}",
    response_model=ArchetypeResponse,
    summary="Update an archetype",
)
async def update_archetype(
    archetype_id: int,
    payload: ArchetypeCreate,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> ArchetypeResponse:
    archetype = await service.update_archetype(archetype_id, payload)
    if not archetype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archetype {archetype_id} not found",
        )
    return archetype


@router.delete(
    "/archetypes/{archetype_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an archetype",
)
async def delete_archetype(
    archetype_id: int,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> None:
    deleted = await service.delete_archetype(archetype_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archetype {archetype_id} not found",
        )


# --------------------------------------------------------------------------
# Fingerprinting endpoints
# --------------------------------------------------------------------------


@router.post(
    "/archetypes/classify/all",
    summary="Fingerprint all unclassified decks",
    description=(
        "Runs the fingerprinting algorithm on every deck that has no archetype_id. "
        "Returns a summary of matched / unmatched / error counts."
    ),
)
async def classify_all(
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> dict:
    return await service.classify_all_unclassified()


@router.post(
    "/archetypes/classify/{deck_id}",
    summary="Fingerprint a single deck",
    description="Assigns archetype_id and deck_key to a deck based on its cards.",
)
async def classify_deck(
    deck_id: int,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> dict:
    from app.a_dal.deck_dal import DeckDAL

    deck_dal = DeckDAL(service.session)
    deck = await deck_dal.get_by_id(deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deck {deck_id} not found",
        )
    matched = await service.classify_deck(deck)
    await service.session.commit()
    return {
        "deck_id": deck_id,
        "deck_key": deck.deck_key,
        "archetype_id": deck.archetype_id,
        "archetype_name": matched.name if matched else None,
    }


# --------------------------------------------------------------------------
# Meta status endpoints
# --------------------------------------------------------------------------


@router.get(
    "/archetypes/meta/{deck_id}",
    response_model=list[DeckMetaStatusResponse],
    summary="Get meta status history for a deck",
)
async def get_meta_history(
    deck_id: int,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> list[DeckMetaStatusResponse]:
    return await service.get_deck_meta_history(deck_id)


@router.post(
    "/archetypes/meta",
    response_model=DeckMetaStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert deck meta status for a season (compute job)",
)
async def upsert_meta_status(
    payload: DeckMetaStatusUpdate,
    service: Annotated[ArchetypeService, Depends(get_archetype_service)],
) -> DeckMetaStatusResponse:
    result = await service.upsert_meta_status(payload)
    await service.session.commit()
    return result
