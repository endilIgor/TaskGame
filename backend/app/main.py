from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import init_database
from backend.app.routers.badges import router as badges_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.missions import router as missions_router
from backend.app.routers.reports import router as reports_router
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

    app.include_router(missions_router)
    app.include_router(badges_router)
    app.include_router(rewards_router)
    app.include_router(dashboard_router)
    app.include_router(reports_router)

    return app


app = create_app()
