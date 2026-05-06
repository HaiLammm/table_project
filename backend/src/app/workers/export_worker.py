import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import structlog

from src.app.db.session import async_session_factory
from src.app.modules.auth.application.services import DataExportService
from src.app.modules.auth.domain.exceptions import DataExportNotFoundError
from src.app.modules.auth.infrastructure.repository import SqlAlchemyUserRepository

logger = structlog.get_logger().bind(module="export_worker")


def _build_archive_entries(payload: dict[str, object]) -> dict[str, object]:
    return {
        "profile.json": payload["profile"],
        "preferences.json": payload["preferences"],
        "vocabulary_terms.json": payload["vocabulary_terms"],
        "review_history.json": payload["review_history"],
        "learning_patterns.json": payload["learning_patterns"],
        "collections.json": payload["collections"],
        "diagnostics.json": payload["diagnostics"],
    }


async def process_data_export(ctx: dict[str, object], export_id: int) -> str:
    _ = ctx

    async with async_session_factory() as session:
        repository = SqlAlchemyUserRepository(session)
        data_export_service = DataExportService(repository, repository, repository)

        try:
            current_export = await data_export_service.get_export_by_id(export_id)
        except DataExportNotFoundError:
            logger.warning("data_export_missing", export_id=export_id)
            return "missing"

        export_path: Path | None = None

        try:
            current_export = await data_export_service.mark_processing(export_id)
            payload = await data_export_service.collect_user_data(current_export.user_id)
            export_path = data_export_service.build_export_path(current_export.user_id, export_id)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            with ZipFile(export_path, mode="w", compression=ZIP_DEFLATED) as archive:
                for filename, content in _build_archive_entries(payload).items():
                    archive.writestr(filename, json.dumps(content, indent=2, ensure_ascii=True))

            await data_export_service.mark_ready(
                export_id=export_id,
                file_path=str(export_path),
                expires_at=data_export_service.build_expiration(),
            )
        except Exception:
            if export_path is not None and export_path.exists():
                export_path.unlink()

            await data_export_service.mark_failed(export_id)
            logger.exception(
                "data_export_processing_failed",
                export_id=export_id,
                user_id=current_export.user_id,
            )
            return "failed"

    logger.info(
        "data_export_processing_ready",
        export_id=export_id,
        user_id=current_export.user_id,
    )
    return "ready"
