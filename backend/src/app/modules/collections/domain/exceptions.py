class CollectionDomainError(Exception):
    status_code = 400
    code = "collection_error"

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class CollectionNotFoundError(CollectionDomainError):
    status_code = 404
    code = "collection_not_found"


class DuplicateCollectionError(CollectionDomainError):
    status_code = 409
    code = "duplicate_collection"


class VocabularyTermNotFoundError(CollectionDomainError):
    status_code = 404
    code = "vocabulary_term_not_found"


class TermAlreadyInCollectionError(CollectionDomainError):
    status_code = 409
    code = "term_already_in_collection"


class TermNotInCollectionError(CollectionDomainError):
    status_code = 404
    code = "term_not_in_collection"
