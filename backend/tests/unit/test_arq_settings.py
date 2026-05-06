from arq.connections import RedisSettings

from src.app.core.config import settings
from src.app.workers.arq_settings import WorkerSettings


def test_worker_settings_use_configured_redis_url() -> None:
    expected = RedisSettings.from_dsn(settings.redis_url)

    assert WorkerSettings.redis_settings.host == expected.host
    assert WorkerSettings.redis_settings.port == expected.port
    assert WorkerSettings.redis_settings.database == expected.database


def test_worker_settings_register_placeholder_job() -> None:
    assert len(WorkerSettings.functions) == 1
    assert WorkerSettings.functions[0].name == "noop"
