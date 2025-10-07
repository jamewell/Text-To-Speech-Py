
from fastapi import APIRouter
from .endpoints import health, auth

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["health"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    auth.router,
    tags=["auth"],
    responses={404: {"description": "Not found"}}
)