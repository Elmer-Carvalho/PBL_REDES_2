from fastapi import APIRouter

from client.app.api.v1.endpoints import stations

api_router = APIRouter()

api_router.include_router(
    stations.router,
    prefix="/stations",
    tags=["stations"]
)
