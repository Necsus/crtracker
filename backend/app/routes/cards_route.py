"""API routes for Clash Royale card listing.

Exposes the cards table so the frontend can display the full card catalogue.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.card_dal import CardDAL
from app.b_models.card import Card as CardModel
from app.database import get_db
from app.schemas import CardResponse

router = APIRouter(prefix="/api/v1", tags=["cards"])


# ==========================================================================
# DEPENDENCY
# ==========================================================================


async def get_card_dal(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardDAL:
    return CardDAL(db)


# ==========================================================================
# HELPERS
# ==========================================================================

_RARITY_MAP: dict[str, str] = {
    "common": "common",
    "rare": "rare",
    "epic": "epic",
    "legendary": "legendary",
    "champion": "champion",
}

_TYPE_MAP: dict[str, str] = {
    "troop": "troop",
    "spell": "spell",
    "building": "building",
}


def _to_response(card: CardModel) -> CardResponse:
    """Map a Card ORM instance to a CardResponse schema."""
    raw_rarity = (card.rarity or "").lower()

    # Prefer card_type column; fall back to raw_data["type"] in case the column
    # was null (e.g. the table was synced before this column was introduced).
    raw_type_src = card.card_type or ((card.raw_data or {}).get("type") or "")
    raw_type = raw_type_src.lower()

    return CardResponse(
        id=str(card.card_id),
        name=card.name,
        elixir=card.elixir_cost or 0,
        rarity=_RARITY_MAP.get(raw_rarity, "common"),  # type: ignore[arg-type]
        type=_TYPE_MAP.get(raw_type),  # type: ignore[arg-type]
        icon_url=card.icon_url_medium,
        description=card.description,
    )


# ==========================================================================
# ENDPOINTS
# ==========================================================================


@router.get(
    "/cards",
    response_model=list[CardResponse],
    summary="List all cards",
    description="Retrieve Clash Royale cards with optional rarity and type filters.",
)
async def list_cards(
    card_dal: Annotated[CardDAL, Depends(get_card_dal)],
    rarity: Annotated[str | None, Query(description="Filter by rarity (e.g. legendary)")] = None,
    type: Annotated[str | None, Query(description="Filter by type (e.g. troop)")] = None,
    q: Annotated[str | None, Query(min_length=1, description="Search by card name")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[CardResponse]:
    """List all cards, with optional rarity/type filters and name search."""
    try:
        if q:
            cards = await card_dal.search(q, offset=offset, limit=limit)
        else:
            cards = await card_dal.list_all(
                rarity=rarity, card_type=type, offset=offset, limit=limit
            )
        return [_to_response(c) for c in cards]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cards: {str(e)}",
        ) from e


@router.get(
    "/cards/{card_id}",
    response_model=CardResponse,
    summary="Get card by CR API id",
    description="Retrieve a single card by its Clash Royale numeric ID.",
)
async def get_card(
    card_id: int,
    card_dal: Annotated[CardDAL, Depends(get_card_dal)],
) -> CardResponse:
    """Return a single card or 404."""
    card = await card_dal.get_by_card_id(card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    return _to_response(card)
