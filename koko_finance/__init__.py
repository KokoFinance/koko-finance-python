"""
Koko Finance Python SDK

Credit card portfolio intelligence — analyze portfolios, compare cards,
get recommendations, and check renewal value.
"""

from .client import KokoClient
from .exceptions import (
    KokoError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ServerError,
)

__version__ = "0.3.0"

__all__ = [
    "KokoClient",
    "KokoError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "ServerError",
]
