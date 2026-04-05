"""Expose the Phase 4c FastAPI package namespace."""

from src.api.main import app, create_app

__all__ = ["app", "create_app"]
