class SrsDomainError(Exception):
    status_code = 400
    code = "srs_error"

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
