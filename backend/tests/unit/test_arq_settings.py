from arq.connections import RedisSettings

from src.app.core.config import settings
from src.app.workers.arq_settings import WorkerSettings


def test_worker_settings_use_configured_redis_url() -> None:
    expected = RedisSettings.from_dsn(settings.redis_url)

    assert WorkerSettings.redis_settings.host == expected.host
    assert WorkerSettings.redis_settings.port == expected.port
    assert WorkerSettings.redis_settings.database == expected.database


def test_worker_settings_registers_enrichment_jobs() -> None:
    function_names = [f.name for f in WorkerSettings.functions]

    assert "noop" in function_names
    assert "process_data_export" in function_names
    assert "process_enrichment_job" in function_names
    assert "process_corpus_sync_job" in function_names

    enrichment_func = next(
        f for f in WorkerSettings.functions if f.name == "process_enrichment_job"
    )
    assert enrichment_func.max_tries == 3

    sync_func = next(f for f in WorkerSettings.functions if f.name == "process_corpus_sync_job")
    assert sync_func.max_tries == 2
