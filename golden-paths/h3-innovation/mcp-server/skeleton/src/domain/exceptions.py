"""Domain exceptions and error handling."""

from typing import Optional


class DomainException(Exception):
    """Base exception for domain layer."""

    def __init__(
        self, message: str, code: Optional[str] = None, details: Optional[dict] = None
    ):
        """
        Initialize domain exception.

        Args:
            message: Human-readable error message
            code: Error code for identification
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class PolicyNotFoundError(DomainException):
    """Raised when a policy is not found."""

    pass


class InvalidPolicyError(DomainException):
    """Raised when a policy is invalid."""

    pass


class ExternalServiceError(DomainException):
    """Raised when external service fails."""

    pass


class ConfigurationError(DomainException):
    """Raised when configuration is invalid."""

    pass
