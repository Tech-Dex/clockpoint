from apscheduler.schedulers.asyncio import AsyncIOScheduler


class APScheduler:
    client: AsyncIOScheduler = None


scheduler = APScheduler()


def get_scheduler() -> AsyncIOScheduler:
    return scheduler.client
