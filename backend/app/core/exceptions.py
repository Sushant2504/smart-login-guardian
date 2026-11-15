"""
Custom exceptions
"""


class AppException(Exception):
    """Base application exception"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedException(AppException):
    """Unauthorized exception"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    """Forbidden exception"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ValidationException(AppException):
    """Validation exception"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class ConflictException(AppException):
    """Conflict exception"""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)
