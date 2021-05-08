import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.scheduler.apscheduler import scheduler


async def connect_scheduler():
    logging.info("APScheduler: Connect scheduler..")
    scheduler.client = AsyncIOScheduler()
    scheduler.client.start()
    logging.info("APScheduler: Connection Successful!")


async def close_scheduler():
    logging.info("APScheduler: Close Connection...")
    scheduler.client.shutdown()
    logging.info("APScheduler: Connection closed!")
