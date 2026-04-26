from fastapi import FastAPI

from app.api.endpoints import blog, campaigns, opportunities, posts, scheduler, signals, subs


def register_routes(app: FastAPI) -> None:
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(posts.router, prefix="/api/v1")
    app.include_router(subs.router, prefix="/api/v1")
    app.include_router(scheduler.router, prefix="/api/v1")
    app.include_router(opportunities.router, prefix="/api/v1")
    app.include_router(signals.router, prefix="/api/v1")
    app.include_router(blog.router, prefix="/api/v1")
