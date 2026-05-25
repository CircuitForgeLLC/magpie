from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import register_routes
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.store import Store
from app.services.scheduler import (
    start_scheduler, stop_scheduler, sync_all_campaigns,
    start_scraper_job,
)

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Run DB migrations
    store = Store(settings.db_path)
    store.run_migrations()

    # Boot scheduler and register all active campaigns
    if settings.scheduler_enabled:
        sched = start_scheduler()
        app.state.scheduler = sched
        campaigns = store.list_campaigns(active_only=True)
        sync_all_campaigns(campaigns)
        logger.info("Magpie started — %d campaign(s) scheduled", len(campaigns))
    else:
        app.state.scheduler = None
        logger.info("Magpie started — scheduler disabled")

    # Start signal scraper job
    if settings.scraper_enabled:
        if not settings.scheduler_enabled:
            # Scraper needs the scheduler even if campaign scheduling is off
            start_scheduler()
        start_scraper_job(interval_mins=settings.scraper_interval_mins)
        logger.info("Signal scraper scheduled every %d min", settings.scraper_interval_mins)

    store.close()
    yield

    # Graceful shutdown
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Magpie",
        description="CircuitForge cross-product social media management",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8531", "http://0.0.0.0:8531"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_routes(app)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
