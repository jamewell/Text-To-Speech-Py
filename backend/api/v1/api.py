
from fastapi import APIRouter
from .endpoints import health, auth, files

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