from fastapi import APIRouter

from app.routers.v1.endpoints.http import auth, clock_entry, debug, group, user

http_router: APIRouter = APIRouter()
HTTP_API_V1: str = "/api/v1"

http_router.include_router(debug.router, prefix="/debug", tags=["Debug"])
http_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
http_router.include_router(user.router, prefix="/user", tags=["User"])
http_router.include_router(group.router, prefix="/group", tags=["Group"])
http_router.include_router(clock_entry.router, prefix="/clock", tags=["Clock Entry"])
