from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)

from src.app.modules.auth.domain.exceptions import AuthenticationError
from src.app.modules.collections.api.dependencies import (
    CurrentUserDependency,
    get_collection_service,
)
from src.app.modules.collections.api.schemas import (
    AddTermRequest,
    AddTermsRequest,
    AddTermsResponse,
    CollectionCreate,
    CollectionCSVImportResponse,
    CollectionListResponse,
    CollectionResponse,
    CollectionTermListResponse,
    CollectionTermResponse,
    CollectionUpdate,
)
from src.app.modules.collections.application.services import CollectionService

router = APIRouter(tags=["collections"])

CollectionServiceDependency = Annotated[CollectionService, Depends(get_collection_service)]
AddTermPayload = Annotated[AddTermRequest | AddTermsRequest, Body()]


def _require_user_id(current_user: CurrentUserDependency) -> int:
    if current_user.id is None:
        msg = "Current user is missing an internal id"
        raise AuthenticationError(msg)

    return current_user.id


def _validate_import_file(file: UploadFile) -> None:
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
    if content_type in allowed_types:
        return

    if file.filename and any(ext in file.filename.lower() for ext in [".csv", ".tsv", ".txt"]):
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": {
                "code": "INVALID_FILE_TYPE",
                "message": "Only CSV, TSV, and TXT files are accepted",
            }
        },
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CollectionResponse)
async def create_collection(
    payload: CollectionCreate,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> CollectionResponse:
    collection = await service.create_collection(
        user_id=_require_user_id(current_user),
        name=payload.name,
        icon=payload.icon,
    )
    return CollectionResponse.model_validate(collection)


@router.get("", response_model=CollectionListResponse)
async def list_collections(
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> CollectionListResponse:
    collections = await service.list_collections(user_id=_require_user_id(current_user))
    return CollectionListResponse(
        items=[CollectionResponse.model_validate(collection) for collection in collections],
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: int,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> CollectionResponse:
    collection = await service.get_collection(
        collection_id=collection_id,
        user_id=_require_user_id(current_user),
    )
    return CollectionResponse.model_validate(collection)


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: int,
    payload: CollectionUpdate,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> CollectionResponse:
    collection = await service.update_collection(
        collection_id=collection_id,
        user_id=_require_user_id(current_user),
        name=payload.name,
        icon=payload.icon,
    )
    return CollectionResponse.model_validate(collection)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> Response:
    await service.delete_collection(
        collection_id=collection_id,
        user_id=_require_user_id(current_user),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{collection_id}/terms",
    status_code=status.HTTP_201_CREATED,
    response_model=AddTermsResponse,
)
async def add_terms_to_collection(
    collection_id: int,
    payload: AddTermPayload,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> AddTermsResponse:
    user_id = _require_user_id(current_user)
    if isinstance(payload, AddTermsRequest):
        result = await service.add_terms_bulk(
            user_id=user_id,
            collection_id=collection_id,
            term_ids=payload.term_ids,
        )
    else:
        result = await service.add_term_to_collection(
            user_id=user_id,
            collection_id=collection_id,
            term_id=payload.term_id,
        )

    return AddTermsResponse.model_validate(result)


@router.delete("/{collection_id}/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_term_from_collection(
    collection_id: int,
    term_id: int,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
) -> Response:
    await service.remove_term_from_collection(
        user_id=_require_user_id(current_user),
        collection_id=collection_id,
        term_id=term_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{collection_id}/terms", response_model=CollectionTermListResponse)
async def get_collection_terms(
    collection_id: int,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CollectionTermListResponse:
    result = await service.get_collection_terms(
        user_id=_require_user_id(current_user),
        collection_id=collection_id,
        page=page,
        page_size=page_size,
    )
    return CollectionTermListResponse(
        items=[CollectionTermResponse.model_validate(item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_next=result["has_next"],
    )


@router.post("/{collection_id}/import", response_model=CollectionCSVImportResponse)
async def import_terms_to_collection(
    collection_id: int,
    current_user: CurrentUserDependency,
    service: CollectionServiceDependency,
    file: Annotated[UploadFile, File(...)],
) -> CollectionCSVImportResponse:
    _validate_import_file(file)
    content = await file.read()
    result = await service.import_csv_to_collection(
        user_id=_require_user_id(current_user),
        collection_id=collection_id,
        file_content=content,
    )
    return CollectionCSVImportResponse.model_validate(result)
