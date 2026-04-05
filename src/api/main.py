"""Build and expose the FastAPI application for Phase 4c endpoints."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.api.routers.audit import analyst_router, audit_router
from src.api.routers.auth import router as auth_router
from src.api.routers.evaluate import router as evaluate_router
from src.db.database import create_db_engine, dispose_engine, initialize_database


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize SQL schema on startup and release bootstrap engine on shutdown."""

    bootstrap_engine = create_db_engine()
    initialize_database(bootstrap_engine)
    try:
        yield
    finally:
        dispose_engine(bootstrap_engine)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(
        title="Loan BRE API",
        version="0.4.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.include_router(auth_router, prefix="/auth")
    app.include_router(evaluate_router, prefix="/v1/evaluate")
    app.include_router(audit_router, prefix="/v1/audit")
    app.include_router(analyst_router, prefix="/v1/analyst")

    return app


app = create_app()
