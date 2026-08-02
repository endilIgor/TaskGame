from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import get_session, init_database
from backend.app.models import PlayerStats
from backend.app.routers.badges import router as badges_router
from backend.app.routers.missions import router as missions_router
from backend.app.routers.rewards import router as rewards_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if app.state.init_db:
        init_database()
    yield


def create_app(init_db: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.init_db = init_db
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    @app.get("/api/dashboard")
    def dashboard(session: Session = Depends(get_session)) -> dict[str, dict[str, int]]:
        player = session.scalar(select(PlayerStats).limit(1))
        return {
            "player": {
                "total_xp": player.total_xp if player else 0,
                "gold": player.gold if player else 0,
            }
        }

    app.include_router(missions_router)
    app.include_router(badges_router)
    app.include_router(rewards_router)

    return app


app = create_app()
