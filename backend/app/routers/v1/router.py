from fastapi import APIRouter

from app.routers.v1.endpoints.http import auth

router_http = APIRouter()
HTTP_API_V1_STR = "/api/v1"

router_ws = APIRouter()
WS_API_V1_STR = "/api/ws/v1"

router_http.include_router(auth.router, prefix="/auth", tags=["Authentication"])
