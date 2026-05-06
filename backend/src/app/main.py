from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.core.config import settings
from src.app.core.exceptions import build_error_payload
from src.app.core.logging import configure_logging
from src.app.modules.auth.api.router import router as auth_router
from src.app.modules.auth.domain.exceptions import AuthDomainError
from src.app.modules.enrichment.api.router import enrichment_router
from src.app.modules.search.api.router import router as search_router
from src.app.modules.srs.api.router import router as srs_router
from src.app.modules.srs.domain.exceptions import SrsDomainError
from src.app.modules.vocabulary.api.router import router as vocabulary_router

health_router = APIRouter()


@health_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


def create_application() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.project_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AuthDomainError)
    async def auth_domain_exception_handler(
        _request: Request,
        exc: AuthDomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(SrsDomainError)
    async def srs_domain_exception_handler(
        _request: Request,
        exc: SrsDomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            content = exc.detail
        else:
            content = build_error_payload("http_error", str(exc.detail))

        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                "validation_error",
                "Request validation failed",
                exc.errors(),
            ),
        )

    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(search_router, prefix=settings.api_v1_prefix)
    app.include_router(srs_router, prefix=f"{settings.api_v1_prefix}/srs_cards")
    app.include_router(vocabulary_router, prefix=f"{settings.api_v1_prefix}/vocabulary_terms")
    app.include_router(enrichment_router, prefix=settings.api_v1_prefix)
    return app


app = create_application()
