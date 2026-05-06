from arq.connections import RedisSettings
from arq.worker import Function, func

from src.app.core.config import settings
from src.app.workers.corpus_sync import process_corpus_sync_job
from src.app.workers.enrichment_worker import process_enrichment_job
from src.app.workers.export_worker import process_data_export


async def noop_job(ctx: dict[str, object]) -> str:
    _ = ctx
    return "noop"


class WorkerSettings:
    functions: list[Function] = [
        func(noop_job, name="noop"),
        func(process_data_export, name="process_data_export"),
        func(process_enrichment_job, name="process_enrichment_job", max_tries=3),
        func(process_corpus_sync_job, name="process_corpus_sync_job", max_tries=2),
    ]
    redis_settings: RedisSettings = RedisSettings.from_dsn(settings.redis_url)
