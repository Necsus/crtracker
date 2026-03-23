"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, computed_field


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int


# =============================================================================
# Player schemas
# =============================================================================


class PlayerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tag: str
    name: str
    exp_level: int
    trophies: int
    best_trophies: int
    wins: int
    losses: int
    battle_count: int
    clan_tag: str | None
    clan_name: str | None
    arena_id: int | None
    arena_name: str | None
    pol_league_number: int | None
    pol_trophies: int | None
    pol_rank: int | None
    last_synced_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def winrate(self) -> float | None:
        if self.battle_count > 0:
            return round(self.wins / self.battle_count * 100, 1)
        return None


class PlayerDetail(PlayerListItem):
    three_crown_wins: int
    challenge_max_wins: int | None
    total_donations: int | None
    donations: int | None
    war_day_wins: int | None
    clan_badge_id: int | None
    role: str | None
    current_deck: list[Any] | None
    current_favourite_card: dict[str, Any] | None
    league_statistics: dict[str, Any] | None
    badges: list[Any] | None
    created_at: datetime


class PlayerSearchResponse(BaseModel):
    players: list[PlayerListItem]
    source: Literal["db", "api"]
    total: int


class PlayerTopResponse(PaginatedResponse):
    items: list[PlayerListItem]
