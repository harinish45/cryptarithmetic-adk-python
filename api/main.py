"""
FastAPI application entrypoint for uvicorn api.main:app.
"""
from api.index import app

__all__ = ["app"]
