import asyncio
import logging

import aioredis
from aredis_om import Migrator
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.core.config import CustomFormatter, settings
from app.core.database.mysql_driver_handler import (
    connect_to_mysql_driver,
    disconnect_from_mysql_driver,
)
from app.core.errors import (
    http_exception_handler,
    internal_server_error_handler,
    not_found_error_handler,
    validation_exception_handler,
)
from app.routers.v1.http_router import HTTP_API_V1, http_router
from app.routers.v1.ws_router import WS_API_V1, ws_router
from app.services.cleaner import remove_inactive_users
from app.services.scheduler import start_clock_session
from app.services.tasks import repeat_every

rootLogger = logging.getLogger()
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(CustomFormatter())
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.DEBUG)

# FastAPI app
app: FastAPI = FastAPI(title=settings.APP_NAME, openapi_url="/api/v1/openapi.json")

# CORS - Set all CORS enabled origins
logging.info("Set all CORS enabled origins")
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def app_startup():
    FastAPICache.init(
        RedisBackend(
            aioredis.from_url(
                settings.REDIS_CACHE_URL, encoding="utf8", decode_responses=True
            )
        ),
        prefix="fastapi-cache",
    )

    await asyncio.gather(connect_to_mysql_driver(), Migrator().run())


async def app_shutdown():
    await asyncio.gather(disconnect_from_mysql_driver())


# App Events
app.add_event_handler("startup", app_startup)
app.add_event_handler("shutdown", app_shutdown)


# Cron Jobs
@app.on_event("startup")
@repeat_every(seconds=settings.DB_CLEANER_CRON_JOB_EVERY_MINUTES, logger=rootLogger)
async def db_cleaner():
    await remove_inactive_users()


@app.on_event("startup")
@repeat_every(
    seconds=settings.CLOCK_SCHEDULER_CRON_JOB_EVERY_MINUTES, logger=rootLogger
)
async def clock_scheduler():
    await start_clock_session()


# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(404, not_found_error_handler)
app.add_exception_handler(500, internal_server_error_handler)

# Routers
app.include_router(http_router, prefix=HTTP_API_V1)
app.include_router(ws_router, prefix=WS_API_V1)
