class SrsDomainError(Exception):
    status_code = 400
    code = "srs_error"

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class CardNotFoundError(SrsDomainError):
    status_code = 404
    code = "card_not_found"


class CardNotDueError(SrsDomainError):
    status_code = 409
    code = "card_not_due"


class DuplicateCardError(SrsDomainError):
    status_code = 409
    code = "duplicate_card"


class NoReviewToUndoError(SrsDomainError):
    status_code = 404
    code = "no_review_to_undo"
