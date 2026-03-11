"""Player API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.player_dal import PlayerDAL
from app.b_models.player import Player
from app.database import get_db
from app.schemas import PlayerCardItem, PlayerListResponse, PlayerResponse

router = APIRouter(prefix="/api/v1/players", tags=["players"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _map_deck(raw: list[dict] | None) -> list[PlayerCardItem]:
    """Convert raw CR API currentDeck card objects → PlayerCardItem."""
    if not raw:
        return []
    result: list[PlayerCardItem] = []
    for c in raw:
        icon_urls = c.get("iconUrls") or {}
        result.append(
            PlayerCardItem(
                id=c.get("id"),
                name=c.get("name", ""),
                elixir_cost=c.get("elixirCost"),
                rarity=c.get("rarity"),
                level=c.get("level"),
                icon_url=icon_urls.get("medium"),
            )
        )
    return result


def _to_response(player: Player) -> PlayerResponse:
    return PlayerResponse(
        tag=player.tag,
        name=player.name,
        trophies=player.trophies,
        best_trophies=player.best_trophies,
        exp_level=player.exp_level,
        wins=player.wins,
        losses=player.losses,
        battle_count=player.battle_count,
        league_number=player.league_number,
        league_rank=player.league_rank,
        season=player.season,
        current_deck=_map_deck(player.current_deck),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=PlayerListResponse)
async def list_players(
    season: str | None = Query(None, description="Filter by season (YYYY-MM)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> PlayerListResponse:
    """Return a paginated leaderboard of players, ordered by league_rank."""
    dal = PlayerDAL(db)
    players = await dal.list_players(season=season, offset=offset, limit=limit)
    total = await dal.count_players(season=season)
    return PlayerListResponse(
        items=list(players),
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/seasons", response_model=list[str])
async def list_seasons(db: AsyncSession = Depends(get_db)) -> list[str]:
    """Return all seasons present in the players table, most recent first."""
    return await PlayerDAL(db).list_seasons()


@router.get("/{tag}", response_model=PlayerResponse)
async def get_player(
    tag: str,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """Return the full profile for a player identified by their battle tag.

    The tag may be provided with or without the leading ``#``.
    E.g. ``/api/v1/players/2YJ08Y9`` or ``/api/v1/players/%232YJ08Y9``.
    """
    player = await PlayerDAL(db).get_by_tag(tag)
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player '{tag}' not found.")
    return _to_response(player)
