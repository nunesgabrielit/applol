from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.dependencies import get_champion_service
from app.routers.champions import router as champions_router
from app.routers.counters import router as counters_router
from app.routers.health import router as health_router
from app.routers.meta import router as meta_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    service = get_champion_service()
    await service.startup()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API e frontend local para analise de draft de League of Legends, "
            "catalogo de campeoes, Champion Deck personalizado e recomendacao "
            "de picks com base em counters."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

    app.include_router(health_router)
    app.include_router(meta_router)
    app.include_router(champions_router)
    app.include_router(counters_router)

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    return app


app = create_app()
