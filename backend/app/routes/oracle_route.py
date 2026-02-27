"""API routes for Oracle matchup analysis.

Provides tactical advice for deck matchups using LLM analysis.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.c_bll.oracle_service import OracleService
from app.database import get_db
from app.schemas import OracleMatchupResponse

router = APIRouter(prefix="/api/v1/oracle", tags=["oracle"])


# ==========================================================================
# DEPENDENCY INJECTION
# ==========================================================================


async def get_oracle_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OracleService:
    """Inject OracleService with database session.

    Args:
        db: Async database session

    Returns:
        Configured OracleService instance
    """
    return OracleService(db)


# ==========================================================================
# ORACLE ENDPOINTS
# ==========================================================================


@router.get(
    "/matchup/{player_deck_id}/{opponent_deck_id}",
    response_model=OracleMatchupResponse,
    summary="Get Oracle matchup analysis",
    description="""Get comprehensive tactical advice for a specific deck matchup.

The Oracle provides an exhaustive list of strategic recommendations including:
- Early game strategy
- Defense priorities
- Counter-attack opportunities
- 2x elixir tactics
- Card-specific tips
- Win conditions

The number of advice items adapts to the matchup complexity.""",
)
async def get_matchup_analysis(
    oracle_service: Annotated[OracleService, Depends(get_oracle_service)],
    player_deck_id: int,
    opponent_deck_id: int,
    force_refresh: Annotated[
        bool,
        Query(
            description="Force regeneration of advice instead of using cached results"
        ),
    ] = False,
) -> OracleMatchupResponse:
    """Get Oracle analysis for a matchup.

    Args:
        oracle_service: Injected oracle service
        player_deck_id: Your deck ID
        opponent_deck_id: Opponent deck ID
        force_refresh: Force regeneration instead of using cache

    Returns:
        Complete Oracle matchup analysis

    Raises:
        HTTPException: If decks not found (404) or analysis fails (500)
    """
    try:
        analysis = await oracle_service.analyze_matchup(
            player_deck_id=player_deck_id,
            opponent_deck_id=opponent_deck_id,
            force_refresh=force_refresh,
        )

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both decks not found",
            )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oracle analysis failed: {str(e)}",
        ) from e
