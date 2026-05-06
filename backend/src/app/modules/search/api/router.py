from typing import Annotated

from fastapi import APIRouter, Query

from src.app.modules.search.api.schemas import (
    SearchPageResponse,
    SearchResponse,
)
from src.app.modules.vocabulary.api.dependencies import VocabularyServiceDependency
from src.app.modules.vocabulary.api.schemas import VocabularyTermResponse

router = APIRouter(tags=["search"])

_STATIC_PAGES: tuple[dict[str, object], ...] = (
    {
        "id": "dashboard",
        "title": "Dashboard",
        "href": "/dashboard",
        "keywords": ("progress", "stats"),
    },
    {
        "id": "vocabulary",
        "title": "Vocabulary",
        "href": "/vocabulary",
        "keywords": ("words", "terms", "search"),
    },
    {
        "id": "collections",
        "title": "Collections",
        "href": "/collections",
        "keywords": ("folders", "study lists"),
    },
    {
        "id": "review",
        "title": "Review",
        "href": "/review",
        "keywords": ("queue", "practice"),
    },
    {
        "id": "diagnostics",
        "title": "Diagnostics",
        "href": "/diagnostics",
        "keywords": ("insights", "analytics"),
    },
    {
        "id": "settings",
        "title": "Settings",
        "href": "/settings",
        "keywords": ("preferences", "profile"),
    },
)


def _match_pages(query: str, limit: int) -> list[SearchPageResponse]:
    normalized_query = query.casefold()
    matches: list[SearchPageResponse] = []

    for page in _STATIC_PAGES:
        haystack = " ".join(
            [
                str(page["title"]),
                str(page["href"]),
                *[str(keyword) for keyword in page["keywords"]],
            ]
        ).casefold()
        if normalized_query in haystack:
            matches.append(
                SearchPageResponse(
                    id=str(page["id"]),
                    title=str(page["title"]),
                    href=str(page["href"]),
                )
            )

    return matches[:limit]


@router.get("/search", response_model=SearchResponse)
async def search_app(
    service: VocabularyServiceDependency,
    query: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SearchResponse:
    vocabulary_results = await service.search_terms(query, limit=limit)

    # TODO: return real collection matches once the collections module exposes searchable data.
    return SearchResponse(
        pages=_match_pages(query, limit),
        collections=[],
        words=[
            VocabularyTermResponse.model_validate(result["term"]) for result in vocabulary_results
        ],
    )
