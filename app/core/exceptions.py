"""Domain-specific exception hierarchy."""


class FNOLBaseError(Exception):
    """Base for all FNOL processing errors."""


class DocumentIngestionError(FNOLBaseError):
    """Raised when PDF cannot be read or is invalid."""


class LLMExtractionError(FNOLBaseError):
    """Raised when the LLM fails to return usable output."""


class LLMUnavailableError(FNOLBaseError):
    """Raised when Ollama service is unreachable."""


class ValidationError(FNOLBaseError):
    """Raised when extracted data fails domain validation."""


class RoutingError(FNOLBaseError):
    """Raised when claim routing cannot be determined."""


class FileSizeLimitError(FNOLBaseError):
    """Raised when uploaded file exceeds size limit."""


class UnsupportedFileTypeError(FNOLBaseError):
    """Raised for non-PDF uploads."""