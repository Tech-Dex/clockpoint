from fastapi import APIRouter

from app.routers.v1.endpoints.http import auth, debug, group

router_http: APIRouter = APIRouter()
HTTP_API_V1: str = "/api/v1"


router_http.include_router(debug.router, prefix="/debug", tags=["Debug"])
router_http.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router_http.include_router(group.router, prefix="/group", tags=["Group"])
