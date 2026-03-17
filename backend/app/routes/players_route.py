"""Player API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.player_dal import PlayerDAL
from app.b_models.player import Player
from app.clients.cr_client import CRApiError, fetch_player
from app.config import Settings
from app.database import get_db
from app.schemas import PlayerCardItem, PlayerListItem, PlayerListResponse, PlayerResponse

log = logging.getLogger(__name__)


def _get_settings() -> Settings:
    from app.config import get_settings
    return get_settings()

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


@router.get("/search", response_model=list[PlayerListItem])
async def search_players(
    q: str = Query(..., min_length=1, description="Name fragment or battle tag (with/without #)"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[PlayerListItem]:
    """Search players by name (partial, case-insensitive) or exact battle tag.

    If the query looks like a battle tag (starts with '#' or is 6-15 alphanumeric
    characters) and yields no DB results, the CR API is queried as a fallback.
    """
    dal = PlayerDAL(db)
    players = await dal.search_players(q, limit=limit)

    if not players:
        # Looks like a tag → try CR API fallback
        looks_like_tag = q.startswith("#") or (q.replace("#", "").isalnum() and 5 <= len(q.lstrip("#")) <= 15)
        if looks_like_tag:
            settings = _get_settings()
            if settings.cr_api_token:
                try:
                    raw = await fetch_player(q, settings.cr_api_token)
                    upserted = await dal.upsert_from_api(raw)
                    return [PlayerListItem.model_validate(upserted)]
                except CRApiError as exc:
                    if exc.status_code != 404:
                        log.warning("CR API search fallback failed: %s", exc)

    return [PlayerListItem.model_validate(p) for p in players]


@router.get("/{tag}", response_model=PlayerResponse)
async def get_player(
    tag: str,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """Return the full profile for a player identified by their battle tag.

    The tag may be provided with or without the leading ``#``.
    If the player is not found locally, the CR API is queried and the result
    is cached in the database for future requests.
    """
    dal = PlayerDAL(db)
    player = await dal.get_by_tag(tag)

    if player is None:
        settings = _get_settings()
        if not settings.cr_api_token:
            raise HTTPException(status_code=404, detail=f"Player '{tag}' not found.")
        try:
            raw = await fetch_player(tag, settings.cr_api_token)
            player = await dal.upsert_from_api(raw)
        except CRApiError as exc:
            if exc.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Player '{tag}' not found.") from exc
            log.error("CR API error while fetching player '%s': %s", tag, exc)
            raise HTTPException(status_code=502, detail="CR API unavailable, try again later.") from exc

    return _to_response(player)
