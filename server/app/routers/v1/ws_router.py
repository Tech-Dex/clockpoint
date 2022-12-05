from fastapi import APIRouter

from app.routers.v1.endpoints.ws import notification

ws_router: APIRouter = APIRouter()
WS_API_V1: str = "/api/v1/ws"

ws_router.include_router(
    notification.router, prefix="/notification", tags=["Notification"]
)
