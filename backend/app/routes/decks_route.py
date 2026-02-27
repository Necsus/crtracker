"""API routes for deck operations.

Handles deck listing, search, statistics, and player import.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.c_bll.deck_service import DeckService
from app.database import get_db
from app.schemas import (
    DeckListItem,
    DeckResponse,
    DeckStatsResponse,
    PlayerImportResponse,
)

router = APIRouter(prefix="/api/v1", tags=["decks"])


# ==========================================================================
# DEPENDENCY INJECTION
# ==========================================================================


async def get_deck_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeckService:
    """Inject DeckService with database session.

    Args:
        db: Async database session

    Returns:
        Configured DeckService instance
    """
    return DeckService(db)


# ==========================================================================
# DECK ENDPOINTS
# ==========================================================================


@router.get(
    "/decks",
    response_model=list[DeckListItem],
    summary="List all decks",
    description="Retrieve a paginated list of all decks in the database.",
)
async def list_decks(
    deck_service: Annotated[DeckService, Depends(get_deck_service)],
    offset: Annotated[int, Query(ge=0, description="Number of decks to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum decks to return")
    ] = 20,
) -> list[DeckListItem]:
    """List all decks with pagination.

    Args:
        deck_service: Injected deck service
        offset: Pagination offset
        limit: Maximum results

    Returns:
        List of deck list items

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        decks, _ = await deck_service.list_decks(offset=offset, limit=limit)
        return decks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve decks: {str(e)}",
        ) from e


@router.get(
    "/decks/search",
    response_model=list[DeckListItem],
    summary="Search decks",
    description="Search decks by name or archetype.",
)
async def search_decks(
    deck_service: Annotated[DeckService, Depends(get_deck_service)],
    query: Annotated[str, Query(min_length=1, description="Search query")] = "",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[DeckListItem]:
    """Search decks by name or archetype.

    Args:
        deck_service: Injected deck service
        query: Search query string
        offset: Pagination offset
        limit: Maximum results

    Returns:
        List of matching deck list items
    """
    try:
        decks, _ = await deck_service.search_decks(query, offset, limit)
        return decks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get(
    "/decks/popular",
    response_model=list[DeckListItem],
    summary="Get popular decks",
    description="Retrieve the most popular decks based on meta share.",
)
async def get_popular_decks(
    deck_service: Annotated[DeckService, Depends(get_deck_service)],
    limit: Annotated[
        int, Query(ge=1, le=50, description="Maximum decks to return")
    ] = 10,
) -> list[DeckListItem]:
    """Get popular decks by meta share.

    Args:
        deck_service: Injected deck service
        limit: Maximum results

    Returns:
        List of popular deck list items
    """
    try:
        return await deck_service.get_popular_decks(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve popular decks: {str(e)}",
        ) from e


@router.get(
    "/deck/{deck_id}",
    response_model=DeckResponse,
    summary="Get deck details",
    description="Retrieve full details of a specific deck.",
)
async def get_deck(
    deck_service: Annotated[DeckService, Depends(get_deck_service)],
    deck_id: int,
) -> DeckResponse:
    """Get a deck by ID.

    Args:
        deck_service: Injected deck service
        deck_id: Deck database ID

    Returns:
        Full deck response

    Raises:
        HTTPException: If deck not found (404) or other error (500)
    """
    deck = await deck_service.get_deck_by_id(deck_id)

    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deck with ID {deck_id} not found",
        )

    return deck


@router.get(
    "/deck/{deck_id}/stats",
    response_model=DeckStatsResponse,
    summary="Get deck statistics",
    description="Retrieve complete statistics for a deck including all matchups.",
)
async def get_deck_stats(
    deck_service: Annotated[DeckService, Depends(get_deck_service)],
    deck_id: int,
) -> DeckStatsResponse:
    """Get statistics for a deck.

    Args:
        deck_service: Injected deck service
        deck_id: Deck database ID

    Returns:
        Complete deck statistics

    Raises:
        HTTPException: If deck not found (404) or other error (500)
    """
    stats = await deck_service.get_deck_statistics(deck_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deck with ID {deck_id} not found",
        )

    return stats


@router.post(
    "/player/import",
    response_model=PlayerImportResponse,
    summary="Import player deck",
    description="Import a deck from a player's profile using their player tag.",
)
async def import_player_deck(
    deck_service: Annotated[DeckService, Depends(get_deck_service)],
    player_tag: str,
) -> PlayerImportResponse:
    """Import a deck from a player profile.

    Args:
        deck_service: Injected deck service
        player_tag: Clash Royale player tag (with or without #)

    Returns:
        Player import response with profile and deck

    Raises:
        HTTPException: If import fails
    """
    try:
        return await deck_service.import_player_deck(player_tag)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import player deck: {str(e)}",
        ) from e
