from fastapi import APIRouter

from app.routers.v1.endpoints.http import auth, group, user

router_http = APIRouter()
HTTP_API_V1_STR = "/api/v1"

router_ws = APIRouter()
WS_API_V1_STR = "/api/ws/v1"

router_http.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router_http.include_router(user.router, prefix="/user", tags=["User"])
router_http.include_router(group.router, prefix="/group", tags=["Group"])
