# Logger
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.core.config import CustomFormatter, Settings
from app.core.errors import (
    http_exception_handler,
    internal_server_error_handler,
    not_found_error_handler,
    validation_exception_handler,
)

# Settings
settings = Settings()

# Logger
logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

# FastAPI app
app = FastAPI(title=settings.APP_NAME, openapi_url="/api/v1/openapi.json")

# CORS - Set all CORS enabled origins
origins = []
logger.info("Set all CORS enabled origins")
if settings.BACKEND_CORS_ORIGINS:
    origins_raw = settings.BACKEND_CORS_ORIGINS.split(",")
    for origin in origins_raw:
        use_origin = origin.strip()
        origins.append(use_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def app_startup():
    ...


async def app_shutdown():
    ...


# App Events
app.add_event_handler("startup", app_startup)
app.add_event_handler("shutdown", app_shutdown)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(404, not_found_error_handler)
app.add_exception_handler(500, internal_server_error_handler)

# Routers
# app.include_router(api_v1_router_http, prefix=HTTP_API_V1_STR)
# app.include_router(api_v1_router_ws, prefix=WS_API_V1_STR)
