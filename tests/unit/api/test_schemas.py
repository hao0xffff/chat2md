"""Unit tests for API schemas."""
import pytest
from datetime import datetime

from app.api.schemas import (
    ExportRequest,
    BatchExportRequest,
    ExportResponse,
    TaskStatusResponse,
    DownloadResponse,
    ErrorResponse,
)


class TestExportRequest:
    """Tests for ExportRequest schema."""

    def test_valid_request(self):
        """Test valid export request."""
        req = ExportRequest(url="https://chatgpt.com/share/abc123")
        assert req.url == "https://chatgpt.com/share/abc123"

    def test_url_validation(self):
        """Test URL is required."""
        with pytest.raises(ValueError):
            ExportRequest()

    def test_url_must_be_string(self):
        """Test URL must be string."""
        with pytest.raises(ValidationError if hasattr(imported_module('pydantic'), 'ValidationError') else ValueError):
            ExportRequest(url=123)


class TestBatchExportRequest:
    """Tests for BatchExportRequest schema."""

    def test_valid_batch_request(self):
        """Test valid batch export request."""
        req = BatchExportRequest(urls=[
            "https://chatgpt.com/share/1",
            "https://chatgpt.com/share/2"
        ])
        assert len(req.urls) == 2

    def test_empty_urls_not_allowed(self):
        """Test empty URLs list is not allowed."""
        with pytest.raises(ValueError):
            BatchExportRequest(urls=[])

    def test_max_urls(self):
        """Test max URLs limit."""
        urls = [f"https://chatgpt.com/share/{i}" for i in range(101)]
        with pytest.raises(ValueError):
            BatchExportRequest(urls=urls)


class TestExportResponse:
    """Tests for ExportResponse schema."""

    def test_response_creation(self):
        """Test creating export response."""
        resp = ExportResponse(
            task_id="task_123",
            status="pending",
            message="Task created"
        )
        assert resp.task_id == "task_123"
        assert resp.status == "pending"
        assert resp.message == "Task created"


class TestTaskStatusResponse:
    """Tests for TaskStatusResponse schema."""

    def test_response_creation(self):
        """Test creating task status response."""
        resp = TaskStatusResponse(
            task_id="task_123",
            status="completed",
            progress=100.0,
            output_path="/output/test",
            message_count=10,
            image_count=5,
            created_at=datetime.now()
        )
        assert resp.task_id == "task_123"
        assert resp.status == "completed"
        assert resp.progress == 100.0

    def test_optional_fields(self):
        """Test optional fields."""
        resp = TaskStatusResponse(
            task_id="task_123",
            status="failed",
            progress=0.0,
            error="Network error",
            created_at=datetime.now()
        )
        assert resp.error == "Network error"
        assert resp.output_path is None


class TestDownloadResponse:
    """Tests for DownloadResponse schema."""

    def test_response_creation(self):
        """Test creating download response."""
        resp = DownloadResponse(
            task_id="task_123",
            output_dir="/output/test",
            file_count=1,
            image_count=5,
            download_url="/files/output/test.zip"
        )
        assert resp.file_count == 1
        assert resp.image_count == 5


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_response_creation(self):
        """Test creating error response."""
        resp = ErrorResponse(
            error="Invalid URL",
            code="VALIDATION_ERROR",
            detail="URL format is invalid"
        )
        assert resp.error == "Invalid URL"
        assert resp.code == "VALIDATION_ERROR"

    def test_detail_optional(self):
        """Test detail is optional."""
        resp = ErrorResponse(error="Error", code="ERROR")
        assert resp.detail is None