from typing import Any, Optional


class AppBaseException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class FileValidationError(AppBaseException):
    """Raised when uploaded file violates validation rules."""
    pass


class IngestionError(AppBaseException):
    """Raised when parsing or loading dataset into DuckDB fails."""
    pass


class LLMProviderError(AppBaseException):
    """Raised when LLM providers fail or cannot fulfill the request."""
    pass


class SQLSecurityError(AppBaseException):
    """Raised when generated or input SQL violates safety constraints."""
    pass
