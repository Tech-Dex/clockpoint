from fastapi import APIRouter

from app.routers.v1.endpoints.http import auth

router_http: APIRouter = APIRouter()
HTTP_API_V1: str = "/api/v1"


router_http.include_router(auth.router, prefix="/auth", tags=["Authentication"])
