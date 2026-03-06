"""Pydantic schemas for request/response validation.

These schemas define the API contract and are automatically
documented in OpenAPI/Swagger.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# CARD SCHEMAS
# =============================================================================


class Card(BaseModel):
    """Represents a single Clash Royale card."""

    id: str = Field(..., description="Unique card identifier (e.g., 'golem')")
    name: str = Field(..., description="Card display name")
    elixir: int = Field(..., ge=0, description="Elixir cost")
    rarity: Literal["common", "rare", "epic", "legendary", "champion"] = Field(
        ..., description="Card rarity"
    )
    type: Literal["troop", "spell", "building"] = Field(
        ..., description="Card type"
    )
    icon_url: str | None = Field(None, description="URL to card icon image")


# =============================================================================
# CARD API RESPONSE SCHEMA
# =============================================================================


class CardResponse(BaseModel):
    """Public response schema for a single Clash Royale card.

    Maps Card DB model fields to the canonical API contract
    (lowercase rarity/type, renamed elixir/icon fields).
    """

    id: str = Field(..., description="CR API card ID as string")
    name: str = Field(..., description="Card display name")
    elixir: int = Field(..., ge=0, description="Elixir cost")
    rarity: Literal["common", "rare", "epic", "legendary", "champion"] = Field(
        ..., description="Card rarity"
    )
    type: Literal["troop", "spell", "building"] | None = Field(
        None, description="Card type"
    )
    icon_url: str | None = Field(None, description="URL to card icon image")
    description: str | None = Field(None, description="In-game card description")

    model_config = {"from_attributes": True}


# =============================================================================
# DECK SCHEMAS
# =============================================================================


class DeckCreate(BaseModel):
    """Schema for creating a new deck."""

    name: str = Field(..., min_length=1, max_length=100, description="Deck name")
    archetype: str = Field(
        ..., min_length=1, max_length=50, description="Archetype (e.g., 'beatdown')"
    )
    cards: list[Card] = Field(..., min_length=8, max_length=8, description="Exactly 8 cards")
    player_tag: str | None = Field(
        None,
        min_length=8,
        max_length=10,
        description="Player tag if imported from profile",
    )


class DeckResponse(BaseModel):
    """Schema for deck response."""

    id: int = Field(..., description="Deck database ID")
    name: str = Field(..., description="Deck name")
    archetype: str = Field(..., description="Archetype")
    cards: list[Card] = Field(..., description="8 cards in the deck")
    avg_elixir: float = Field(..., description="Average elixir cost")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class DeckListItem(BaseModel):
    """Lightweight schema for deck list views."""

    id: int
    name: str
    archetype: str
    avg_elixir: float
    card_count: int = Field(..., description="Always 8")


# =============================================================================
# MATCHUP STATISTICS SCHEMAS
# =============================================================================


class MatchupStats(BaseModel):
    """Statistics for a deck vs deck matchup."""

    opponent_deck_id: int = Field(..., description="Opponent deck ID")
    opponent_deck_name: str = Field(..., description="Opponent deck name")
    opponent_archetype: str = Field(..., description="Opponent archetype")
    winrate: float = Field(
        ..., ge=0, le=100, description="Win percentage (0-100)"
    )
    sample_size: int = Field(
        ..., ge=0, description="Number of recorded matches"
    )
    top_1000_winrate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Winrate in Top 1000 ladder matches",
    )
    last_updated: datetime = Field(..., description="Last stats update")


class DeckStatsResponse(BaseModel):
    """Complete statistics for a deck."""

    deck: DeckResponse
    matchups: list[MatchupStats] = Field(
        ..., description="List of matchup statistics vs meta decks"
    )
    global_winrate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall winrate across all matchups",
    )
    meta_share: float = Field(
        ...,
        ge=0,
        le=100,
        description="Meta usage percentage",
    )


# =============================================================================
# ORACLE SCHEMAS
# =============================================================================


class OracleAdviceCategory(BaseModel):
    """Category of tactical advice."""

    name: str = Field(..., description="Category name (e.g., 'Early Game')")
    priority: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Advice priority level"
    )


class OracleAdvice(BaseModel):
    """Single tactical advice from the Oracle."""

    id: str = Field(..., description="Unique advice identifier")
    category: OracleAdviceCategory = Field(..., description="Advice category")
    title: str = Field(..., description="Short descriptive title")
    description: str = Field(..., description="Detailed tactical advice")
    cards_involved: list[str] = Field(
        ..., description="Card IDs relevant to this advice"
    )
    timing: str | None = Field(
        None,
        description="When to apply (e.g., 'At 2x elixir')",
    )


class OracleMatchupResponse(BaseModel):
    """Complete Oracle analysis for a matchup."""

    player_deck: DeckResponse
    opponent_deck: DeckResponse
    winrate_prediction: float = Field(
        ..., ge=0, le=100, description="Predicted winrate"
    )
    difficulty: Literal["favorable", "even", "unfavorable", "hard"] = Field(
        ..., description="Matchup difficulty"
    )
    advice: list[OracleAdvice] = Field(
        ..., description="Exhaustive list of tactical advice"
    )
    generated_at: datetime = Field(default_factory=datetime.now)
    source: Literal["cached", "llm", "mock"] = Field(
        ..., description="Advice source"
    )


class OracleRequest(BaseModel):
    """Request for Oracle analysis."""

    player_deck_id: int = Field(..., description="Your deck ID")
    opponent_deck_id: int = Field(..., description="Opponent deck ID")
    force_refresh: bool = Field(
        default=False,
        description="Force regeneration instead of using cache",
    )


# =============================================================================
# PLAYER SCHEMAS
# =============================================================================


class PlayerProfile(BaseModel):
    """Clash Royale player profile."""

    tag: str = Field(..., description="Player tag")
    name: str = Field(..., description="Player name")
    trophies: int = Field(..., ge=0, description="Current trophies")
    best_trophies: int = Field(..., ge=0, description="Best trophies")
    arena: str = Field(..., description="Current arena/league")
    wins: int = Field(..., ge=0, description="Total wins")
    losses: int = Field(..., ge=0, description="Total losses")
    current_deck: list[Card] | None = Field(None, description="Current battle deck")


class PlayerImportResponse(BaseModel):
    """Response after importing player deck."""

    player: PlayerProfile
    deck: DeckResponse | None = Field(None, description="Imported deck if available")
    message: str = Field(..., description="Status message")


# =============================================================================
# COMMON SCHEMAS
# =============================================================================


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: str | None = Field(None, description="Additional error details")
