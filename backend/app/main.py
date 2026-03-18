"""CRTracker FastAPI Application.

Main entry point for the CRTracker API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.archetypes_route import router as archetypes_router
from app.routes.battles_route import router as battles_router
from app.routes.cards_route import router as cards_router
from app.routes.decks_route import router as decks_router
from app.routes.oracle_route import router as oracle_router
from app.routes.players_route import router as players_router

settings = get_settings()


# ==========================================================================
# LIFESPAN EVENTS
# ==========================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print(f"🎮 {settings.app_name} v{settings.app_version} starting...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔧 Debug mode: {settings.debug}")

    yield

    # Shutdown
    print(f"🎮 {settings.app_name} shutting down...")


# ==========================================================================
# APPLICATION FACTORY
# ==========================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="""
        CRTracker API - Strategic assistant for Clash Royale players

        ## Features

        * **Decks**: Browse and search decks from the Top 1000 meta
        * **Statistics**: View detailed matchup statistics and winrates
        * **Oracle**: Get AI-powered tactical advice for any matchup
        * **Player Import**: Import decks directly from player profiles

        ## Architecture

        Built with Clean Architecture principles:
        * FastAPI framework
        * PostgreSQL with SQLAlchemy 2.0 async
        * Pydantic v2 for validation
        * LLM integration for Oracle analysis
        """,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # ==========================================================================
    # CORS MIDDLEWARE
    # ==========================================================================

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==========================================================================
    # ROUTE REGISTRATION
    # ==========================================================================

    app.include_router(archetypes_router)
    app.include_router(battles_router)
    app.include_router(cards_router)
    app.include_router(decks_router)
    app.include_router(oracle_router)
    app.include_router(players_router)

    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================

    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "CRTracker API",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "disabled",
        }

    return app


# ==========================================================================
# APPLICATION INSTANCE
# ==========================================================================

app = create_app()


# ==========================================================================
# DEVELOPMENT SERVER
# ==========================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
