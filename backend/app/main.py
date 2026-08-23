from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope
from starlette.responses import Response

from backend.app.config import get_settings
from backend.app.database import init_database
from backend.app.routers.badges import router as badges_router
from backend.app.routers.backup import router as backup_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.journal import router as journal_router
from backend.app.routers.missions import router as missions_router
from backend.app.routers.profile import router as profile_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.rewards import router as rewards_router


APP_DISPLAY_NAME = "NagiGame"


class NoCacheStaticFiles(StaticFiles):
    """Serves frontend/dist without letting browsers/proxies cache stale builds.

    A prior rebuild would silently keep serving an old index.html/bundle from
    cache, so every response from this mount gets explicit no-store headers.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if app.state.init_db:
        init_database()
    yield


def create_app(init_db: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=APP_DISPLAY_NAME, lifespan=lifespan)
    app.state.init_db = init_db
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": APP_DISPLAY_NAME}

    app.include_router(missions_router)
    app.include_router(backup_router)
    app.include_router(badges_router)
    app.include_router(rewards_router)
    app.include_router(dashboard_router)
    app.include_router(reports_router)
    app.include_router(journal_router)
    app.include_router(profile_router)
    app.mount("/", NoCacheStaticFiles(directory="frontend/dist", html=True), name="frontend")

    return app


app = create_app()
