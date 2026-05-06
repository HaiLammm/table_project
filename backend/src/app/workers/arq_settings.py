from arq.connections import RedisSettings
from arq.worker import Function, func

from src.app.core.config import settings
from src.app.workers.export_worker import process_data_export


async def noop_job(ctx: dict[str, object]) -> str:
    _ = ctx
    return "noop"


class WorkerSettings:
    functions: list[Function] = [
        func(noop_job, name="noop"),
        func(process_data_export, name="process_data_export"),
    ]
    redis_settings: RedisSettings = RedisSettings.from_dsn(settings.redis_url)
