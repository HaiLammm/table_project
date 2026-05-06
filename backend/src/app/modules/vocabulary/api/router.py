from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from src.app.modules.vocabulary.api.dependencies import VocabularyServiceDependency
from src.app.modules.vocabulary.api.schemas import (
    VocabularyDefinitionResponse,
    VocabularyFilterParams,
    VocabularySearchParams,
    VocabularyTermListResponse,
    VocabularyTermResponse,
)

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
