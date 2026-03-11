"""Battle log API routes."""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.battle_dal import BattleDal
from app.b_models.battle import Battle
from app.b_models.card import Card
from app.database import get_db
from app.schemas import BattleCardItem, BattleListResponse, BattleResponse

router = APIRouter(prefix="/api/v1/battles", tags=["battles"])


async def _build_icon_lookup(db: AsyncSession, battles: Sequence[Battle]) -> dict[int, str]:
    """Return {numeric_card_id: icon_url_medium} for all cards that appear in the given battles."""
    ids: set[int] = set()
    for b in battles:
        for col in (b.team1_cards, b.team2_cards):
            if isinstance(col, list):
                for c in col:
                    if isinstance(c, dict) and c.get("id"):
                        ids.add(int(c["id"]))
    if not ids:
        return {}
    result = await db.execute(
        select(Card.card_id, Card.icon_url_medium).where(Card.card_id.in_(ids))
    )
    return {row.card_id: row.icon_url_medium for row in result if row.icon_url_medium}


def _map_cards(raw: list[dict] | None, icon_lookup: dict[int, str]) -> list[BattleCardItem]:
    """Convert raw CR API card objects → BattleCardItem, enriching icon_url from the cards table."""
    if not raw:
        return []
    result: list[BattleCardItem] = []
    for c in raw:
        card_id = c.get("id", 0)
        # Prefer icon from our cards table (always present); fall back to raw iconUrls
        icon_url = icon_lookup.get(int(card_id)) if card_id else None
        if not icon_url:
            icon_urls = c.get("iconUrls") or {}
            icon_url = icon_urls.get("medium")
        result.append(
            BattleCardItem(
                id=card_id,
                name=c.get("name", ""),
                elixir_cost=c.get("elixirCost"),
                rarity=c.get("rarity"),
                level=c.get("level"),
                icon_url=icon_url,
            )
        )
    return result


def _to_response(battle: Battle, icon_lookup: dict[int, str]) -> BattleResponse:
    return BattleResponse(
        id=battle.id,
        battle_key=battle.battle_key,
        battle_time=battle.battle_time,
        battle_type=battle.battle_type,
        game_mode_name=battle.game_mode_name,
        arena_name=battle.arena_name,
        team1_tag=battle.team1_tag,
        team1_name=battle.team1_name,
        team1_crowns=battle.team1_crowns,
        team1_starting_trophies=battle.team1_starting_trophies,
        team1_trophy_change=battle.team1_trophy_change,
        team1_cards=_map_cards(battle.team1_cards, icon_lookup),
        team2_tag=battle.team2_tag,
        team2_name=battle.team2_name,
        team2_crowns=battle.team2_crowns,
        team2_starting_trophies=battle.team2_starting_trophies,
        team2_trophy_change=battle.team2_trophy_change,
        team2_cards=_map_cards(battle.team2_cards, icon_lookup),
        winner_tag=battle.winner_tag,
    )


@router.get("", response_model=BattleListResponse)
async def list_battles(
    battle_type: str | None = Query(None, description="Filter by battle type, e.g. 'pathOfLegend'"),
    deck_id: int | None = Query(None, description="Filter battles where this deck (by ID) was used by either team"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BattleListResponse:
    dal = BattleDal(db)

    if deck_id is not None:
        from app.a_dal.deck_dal import DeckDAL
        from app.c_bll.deck_service import DeckService

        deck = await DeckDAL(db).get_by_id(deck_id)
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")
        cards = DeckService._extract_cards(deck.cards)
        card_names = [c["name"] for c in cards]
        battles = await dal.list_battles_by_card_names(card_names, offset, limit)
        total = await dal.count_battles_by_card_names(card_names)
    else:
        battles = await dal.list_battles(battle_type, offset, limit)
        total = await dal.count_battles(battle_type)

    icon_lookup = await _build_icon_lookup(db, battles)
    return BattleListResponse(
        items=[_to_response(b, icon_lookup) for b in battles],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/types", response_model=list[str])
async def list_battle_types(db: AsyncSession = Depends(get_db)) -> list[str]:
    return await BattleDal(db).list_battle_types()
