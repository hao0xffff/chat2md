"""Exception hierarchy for the application."""
from app.domain.model.knowledge_document import KnowledgeDocument
from app.domain.model.image_resource import ImageResource


class BusinessException(Exception):
    """Base exception for all business exceptions."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or "BUSINESS_ERROR"
        super().__init__(self.message)


class ParserException(BusinessException):
    """Exception raised when parsing fails."""

    def __init__(
        self,
        message: str,
        parser_type: str | None = None,
        url: str | None = None
    ):
        super().__init__(message, code="PARSER_ERROR")
        self.parser_type = parser_type
        self.url = url


class PlatformNotSupportedException(ParserException):
    """Exception raised when a platform is not supported."""

    def __init__(self, url_or_platform: str, supported_platforms: list[str]):
        super().__init__(
            message=f"Platform not supported: {url_or_platform}",
            url=url_or_platform if "://" in url_or_platform else None
        )
        self.supported_platforms = supported_platforms


class DownloadException(BusinessException):
    """Exception raised when download fails."""

    def __init__(
        self,
        message: str,
        resource_url: str | None = None,
        status_code: int | None = None
    ):
        super().__init__(message, code="DOWNLOAD_ERROR")
        self.resource_url = resource_url
        self.status_code = status_code


class ExportException(BusinessException):
    """Exception raised when export fails."""

    def __init__(self, message: str, output_path: str | None = None):
        super().__init__(message, code="EXPORT_ERROR")
        self.output_path = output_path


class ValidationException(BusinessException):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field


class TaskNotFoundException(BusinessException):
    """Exception raised when a task is not found."""

    def __init__(self, task_id: str):
        super().__init__(message=f"Task not found: {task_id}", code="TASK_NOT_FOUND")
        self.task_id = task_id


class TaskNotCompletedException(BusinessException):
    """Exception raised when trying to download an incomplete task."""

    def __init__(self, task_id: str, status: str):
        super().__init__(
            message=f"Task not completed: {task_id} (status: {status})",
            code="TASK_NOT_COMPLETED"
        )
        self.task_id = task_id
        self.status = status