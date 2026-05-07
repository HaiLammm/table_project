class DashboardDomainError(Exception):
    status_code = 400
    code = "dashboard_error"

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InsufficientDataError(DashboardDomainError):
    status_code = 422
    code = "insufficient_review_data"


class InsightNotFoundError(DashboardDomainError):
    status_code = 404
    code = "insight_not_found"
