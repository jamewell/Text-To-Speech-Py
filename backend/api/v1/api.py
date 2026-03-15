
from fastapi import APIRouter
from .endpoints import health, auth, files, chapters

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["health"]
)

api_router.include_router(
    auth.router,
    tags=["auth"]
)

api_router.include_router(
    files.router,
    prefix="/files",
    tags=["files"]
)

api_router.include_router(
    chapters.router,
    prefix="/chapters",
    tags=["chapters"]
)