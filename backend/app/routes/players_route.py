"""Players API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.c_bll.player_service import PlayerService
from app.clients.cr_client import CRApiError
from app.config import get_settings
from app.database import get_db
from app.schemas import BattleItem, BattleListResponse, PlayerDetail, PlayerListItem, PlayerSearchResponse, PlayerTopResponse

router = APIRouter(prefix="/api/v1/players", tags=["players"])
settings = get_settings()


def _get_service(db: AsyncSession = Depends(get_db)) -> PlayerService:
    return PlayerService(db, settings.cr_api_token)


@router.get("", response_model=PlayerTopResponse)
async def list_top_players(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: PlayerService = Depends(_get_service),
):
    offset = (page - 1) * page_size
    players, total = await service.list_top(limit=page_size, offset=offset)
    return PlayerTopResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[PlayerListItem.model_validate(p) for p in players],
    )


@router.get("/search", response_model=PlayerSearchResponse)
async def search_players(
    q: str = Query(..., min_length=1, max_length=50),
    service: PlayerService = Depends(_get_service),
):
    try:
        players, source = await service.search(q)
    except CRApiError as exc:
        raise HTTPException(status_code=502, detail=f"CR API error: {exc}")
    return PlayerSearchResponse(
        players=[PlayerListItem.model_validate(p) for p in players],
        source=source,
        total=len(players),
    )


@router.get("/{tag}", response_model=PlayerDetail)
async def get_player(
    tag: str,
    service: PlayerService = Depends(_get_service),
):
    try:
        player = await service.get_or_fetch(tag)
    except CRApiError as exc:
        if exc.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found")
        raise HTTPException(status_code=502, detail=f"CR API error: {exc}")
    return PlayerDetail.model_validate(player)


@router.get("/{tag}/battles", response_model=BattleListResponse)
async def get_player_battles(
    tag: str,
    limit: int = Query(25, ge=1, le=100),
    service: PlayerService = Depends(_get_service),
):
    battles = await service.list_battles(tag, limit=limit)
    return BattleListResponse(
        battles=[BattleItem.model_validate(b) for b in battles],
        total=len(battles),
    )
