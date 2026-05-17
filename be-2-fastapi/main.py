"""Uvicorn entrypoint: `uvicorn main:app` (re-exports app from package)."""

from app.main import app

__all__ = ["app"]
