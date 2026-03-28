"""CRTracker FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.players_route import router as players_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.app_name} v{settings.app_version} starting...")
    yield
    print(f"{settings.app_name} shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
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

    app.include_router(players_router)

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "app": settings.app_name, "version": settings.app_version}

    @app.get("/", tags=["root"])
    async def root():
        return {"message": "CRTracker API", "version": settings.app_version}

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
