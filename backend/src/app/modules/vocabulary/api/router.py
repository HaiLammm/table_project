from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from src.app.modules.vocabulary.api.dependencies import VocabularyServiceDependency
from src.app.modules.vocabulary.api.schemas import (
    CSVImportPreviewResponse,
    CSVImportResultResponse,
    CSVRowPreview,
    VocabularyDefinitionResponse,
    VocabularyFilterParams,
    VocabularySearchParams,
    VocabularyTermCreateRequest,
    VocabularyTermListResponse,
    VocabularyTermResponse,
)
from src.app.modules.vocabulary.application.csv_parser import parse_csv
from src.app.modules.vocabulary.domain.exceptions import DuplicateTermError

router = APIRouter(tags=["vocabulary"])


@router.get("", response_model=VocabularyTermListResponse)
async def list_vocabulary_terms(
    service: VocabularyServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    cefr_level: Annotated[str | None, Query()] = None,
    jlpt_level: Annotated[str | None, Query()] = None,
    parent_id: Annotated[int | None, Query()] = None,
) -> VocabularyTermListResponse:
    result = await service.list_terms(
        page=page,
        page_size=page_size,
        cefr_level=cefr_level,
        jlpt_level=jlpt_level,
        parent_id=parent_id,
    )
    return VocabularyTermListResponse(
        items=[VocabularyTermResponse.model_validate(t) for t in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_next=result["has_next"],
    )


@router.get("/search", response_model=VocabularyTermListResponse)
async def search_vocabulary_terms(
    service: VocabularyServiceDependency,
    query: Annotated[str, Query(min_length=1)],
    language: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> VocabularyTermListResponse:
    results = await service.search_terms(query, language=language, limit=limit)
    items = [r["term"] for r in results]
    return VocabularyTermListResponse(
        items=[VocabularyTermResponse.model_validate(t) for t in items],
        total=len(items),
        page=1,
        page_size=limit,
        has_next=False,
    )


@router.get("/{term_id}", response_model=VocabularyTermResponse)
async def get_vocabulary_term(
    service: VocabularyServiceDependency,
    term_id: int,
) -> VocabularyTermResponse:
    term = await service.get_term_by_id(term_id)
    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TERM_NOT_FOUND",
                    "message": f"Term with id {term_id} not found",
                    "details": None,
                }
            },
        )
    return VocabularyTermResponse.model_validate(term)


@router.get("/{term_id}/children", response_model=VocabularyTermListResponse)
async def get_vocabulary_term_children(
    service: VocabularyServiceDependency,
    term_id: int,
) -> VocabularyTermListResponse:
    children = await service.get_children(term_id)
    return VocabularyTermListResponse(
        items=[VocabularyTermResponse.model_validate(t) for t in children],
        total=len(children),
        page=1,
        page_size=len(children),
        has_next=False,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VocabularyTermResponse)
async def create_vocabulary_term(
    payload: VocabularyTermCreateRequest,
    service: VocabularyServiceDependency,
) -> VocabularyTermResponse:
    try:
        term = await service.create_user_term(
            term=payload.term,
            language=payload.language,
            definition=payload.definition,
            cefr_level=payload.cefr_level,
            jlpt_level=payload.jlpt_level,
            part_of_speech=payload.part_of_speech,
        )
        return VocabularyTermResponse.model_validate(term)
    except DuplicateTermError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "DUPLICATE_TERM",
                    "message": "This term already exists in your vocabulary",
                }
            },
        )


@router.post("/import/preview")
async def preview_csv_import(
    service: VocabularyServiceDependency,
    file: UploadFile,
) -> CSVImportPreviewResponse:
    if file.size is not None and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "File exceeds maximum size of 10MB",
                }
            },
        )

    allowed_types = {"text/csv", "text/tab-separated", "text/plain", "application/csv"}
    content_type = file.content_type or ""
    if content_type not in allowed_types and not (
        file.filename and any(ext in file.filename.lower() for ext in [".csv", ".tsv", ".txt"])
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "Only CSV, TSV, and TXT files are accepted",
                }
            },
        )

    content = await file.read()
    parse_result = parse_csv(content)

    preview_rows = [
        CSVRowPreview(
            row_number=row.row_number,
            term=row.term,
            language=row.language,
            definition=row.definition,
            tags="::".join(row.tags) if row.tags else None,
            status=row.status,
            error_message=row.error_message,
        )
        for row in parse_result.rows[:10]
    ]

    return CSVImportPreviewResponse(
        total_rows=parse_result.total_rows,
        valid_count=parse_result.valid_count,
        warning_count=parse_result.warning_count,
        error_count=parse_result.error_count,
        preview_rows=preview_rows,
        detected_columns=parse_result.detected_columns,
    )


@router.post("/import", response_model=CSVImportResultResponse)
async def import_csv(
    service: VocabularyServiceDependency,
    file: UploadFile,
) -> CSVImportResultResponse:
    if file.size is not None and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "File exceeds maximum size of 10MB",
                }
            },
        )

    allowed_types = {"text/csv", "text/tab-separated", "text/plain", "application/csv"}
    content_type = file.content_type or ""
    if content_type not in allowed_types and not (
        file.filename and any(ext in file.filename.lower() for ext in [".csv", ".tsv", ".txt"])
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "Only CSV, TSV, and TXT files are accepted",
                }
            },
        )

    content = await file.read()
    parse_result = parse_csv(content)

    result = await service.import_csv(parse_result)

    return CSVImportResultResponse(
        imported_count=result["imported_count"],
        review_count=result["review_count"],
        duplicates_skipped=result["duplicates_skipped"],
        errors=result["errors"],
    )
