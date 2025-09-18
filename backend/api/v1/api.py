
from fastapi import APIRouter
from .endpoints import health


api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["health"],
    responses={404: {"description": "Not found"}}
)