"""Battle log API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.battle_dal import BattleDal
from app.b_models.battle import Battle
from app.database import get_db
from app.schemas import BattleCardItem, BattleListResponse, BattleResponse

router = APIRouter(prefix="/api/v1/battles", tags=["battles"])


def _map_cards(raw: list[dict] | None) -> list[BattleCardItem]:
    """Convert raw CR API card objects → BattleCardItem."""
    if not raw:
        return []
    result: list[BattleCardItem] = []
    for c in raw:
        icon_urls = c.get("iconUrls") or {}
        result.append(
            BattleCardItem(
                id=c.get("id", 0),
                name=c.get("name", ""),
                elixir_cost=c.get("elixirCost"),
                rarity=c.get("rarity"),
                level=c.get("level"),
                icon_url=icon_urls.get("medium"),
            )
        )
    return result


def _to_response(battle: Battle) -> BattleResponse:
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
        team1_cards=_map_cards(battle.team1_cards),
        team2_tag=battle.team2_tag,
        team2_name=battle.team2_name,
        team2_crowns=battle.team2_crowns,
        team2_starting_trophies=battle.team2_starting_trophies,
        team2_trophy_change=battle.team2_trophy_change,
        team2_cards=_map_cards(battle.team2_cards),
        winner_tag=battle.winner_tag,
    )


@router.get("", response_model=BattleListResponse)
async def list_battles(
    battle_type: str | None = Query(None, description="Filter by battle type, e.g. 'pathOfLegend'"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BattleListResponse:
    dal = BattleDal(db)
    battles, total = await dal.list_battles(battle_type, offset, limit), await dal.count_battles(battle_type)
    return BattleListResponse(
        items=[_to_response(b) for b in battles],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/types", response_model=list[str])
async def list_battle_types(db: AsyncSession = Depends(get_db)) -> list[str]:
    return await BattleDal(db).list_battle_types()
