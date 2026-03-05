"""
Typed exceptions for the Koko Finance API.

Maps HTTP status codes to specific exception types for clean error handling.
"""


class KokoError(Exception):
    """Base exception for Koko API errors."""

    def __init__(self, message: str, status_code: int = None, request_id: str = None):
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        super().__init__(message)

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"


class AuthenticationError(KokoError):
    """Raised when API key is invalid or missing (401)."""
    pass


class RateLimitError(KokoError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(KokoError):
    """Raised when request parameters are invalid (400/422)."""
    pass


class ServerError(KokoError):
    """Raised when the API returns a server error (500)."""
    pass
