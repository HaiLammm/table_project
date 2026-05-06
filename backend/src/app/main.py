from fastapi import APIRouter, FastAPI

from src.app.core.config import settings
from src.app.core.logging import configure_logging

health_router = APIRouter()


@health_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


def create_application() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.project_name)
    app.include_router(health_router, prefix=settings.api_v1_prefix)
    return app


app = create_application()
