"""Unit tests for exception hierarchy."""
import pytest

from app.common.exceptions import (
    BusinessException,
    ParserException,
    PlatformNotSupportedException,
    DownloadException,
    ExportException,
    ValidationException,
    TaskNotFoundException,
    TaskNotCompletedException,
)


class TestBusinessException:
    """Tests for BusinessException."""

    def test_creation(self):
        """Test basic exception creation."""
        exc = BusinessException("Something went wrong")
        assert exc.message == "Something went wrong"
        assert exc.code == "BUSINESS_ERROR"

    def test_custom_code(self):
        """Test custom error code."""
        exc = BusinessException("Error", code="CUSTOM_CODE")
        assert exc.code == "CUSTOM_CODE"

    def test_is_exception(self):
        """Test it is an Exception subclass."""
        assert isinstance(BusinessException("Error"), Exception)


class TestParserException:
    """Tests for ParserException."""

    def test_creation(self):
        """Test parser exception creation."""
        exc = ParserException(
            message="Parse failed",
            parser_type="ChatGPTParser",
            url="https://chatgpt.com/share/abc"
        )
        assert exc.message == "Parse failed"
        assert exc.parser_type == "ChatGPTParser"
        assert exc.url == "https://chatgpt.com/share/abc"
        assert exc.code == "PARSER_ERROR"


class TestPlatformNotSupportedException:
    """Tests for PlatformNotSupportedException."""

    def test_creation(self):
        """Test platform not supported exception."""
        exc = PlatformNotSupportedException(
            url_or_platform="https://unknown.com/share/abc",
            supported_platforms=["chatgpt", "gemini", "doubao"]
        )
        assert "unknown.com" in exc.message
        assert exc.supported_platforms == ["chatgpt", "gemini", "doubao"]


class TestDownloadException:
    """Tests for DownloadException."""

    def test_creation(self):
        """Test download exception creation."""
        exc = DownloadException(
            message="Download failed",
            resource_url="https://example.com/image.png",
            status_code=404
        )
        assert exc.message == "Download failed"
        assert exc.resource_url == "https://example.com/image.png"
        assert exc.status_code == 404
        assert exc.code == "DOWNLOAD_ERROR"


class TestExportException:
    """Tests for ExportException."""

    def test_creation(self):
        """Test export exception creation."""
        exc = ExportException(
            message="Export failed",
            output_path="/output/test"
        )
        assert exc.message == "Export failed"
        assert exc.output_path == "/output/test"
        assert exc.code == "EXPORT_ERROR"


class TestValidationException:
    """Tests for ValidationException."""

    def test_creation(self):
        """Test validation exception creation."""
        exc = ValidationException(
            message="Invalid input",
            field="url"
        )
        assert exc.message == "Invalid input"
        assert exc.field == "url"
        assert exc.code == "VALIDATION_ERROR"

    def test_without_field(self):
        """Test validation exception without field."""
        exc = ValidationException(message="Invalid input")
        assert exc.field is None


class TestTaskNotFoundException:
    """Tests for TaskNotFoundException."""

    def test_creation(self):
        """Test task not found exception."""
        exc = TaskNotFoundException(task_id="task_123")
        assert exc.task_id == "task_123"
        assert "task_123" in exc.message
        assert exc.code == "TASK_NOT_FOUND"


class TestTaskNotCompletedException:
    """Tests for TaskNotCompletedException."""

    def test_creation(self):
        """Test task not completed exception."""
        exc = TaskNotCompletedException(
            task_id="task_123",
            status="parsing"
        )
        assert exc.task_id == "task_123"
        assert exc.status == "parsing"
        assert "parsing" in exc.message
        assert exc.code == "TASK_NOT_COMPLETED"