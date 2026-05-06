class AuthDomainError(Exception):
    status_code = 400
    code = "auth_error"

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class AuthenticationError(AuthDomainError):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(AuthDomainError):
    status_code = 403
    code = "authorization_error"


class UserNotFoundError(AuthenticationError):
    code = "user_not_found"
