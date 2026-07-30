"""Root entrypoint exporting FastAPI app for Vercel / serverless deployments."""

from backend.main import app

__all__ = ["app"]
