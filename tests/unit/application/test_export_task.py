"""Unit tests for ExportTask model."""
import pytest
from datetime import datetime

from app.application.export_task import ExportTask, ExportTaskStatus


class TestExportTask:
    """Tests for ExportTask model."""

    def test_creation(self):
        """Test basic task creation."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        assert task.id is not None
        assert task.url == "https://chatgpt.com/share/abc123"
        assert task.status == ExportTaskStatus.PENDING
        assert task.progress == 0.0
        assert task.error is None

    def test_update_progress(self):
        """Test progress update."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.update_progress(50.0)
        assert task.progress == 50.0

    def test_update_progress_clamps_values(self):
        """Test progress is clamped between 0 and 100."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.update_progress(150.0)
        assert task.progress == 100.0

        task.update_progress(-10.0)
        assert task.progress == 0.0

    def test_mark_parsing(self):
        """Test marking task as parsing."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.mark_parsing()

        assert task.status == ExportTaskStatus.PARSING
        assert task.progress == 10.0

    def test_mark_downloading(self):
        """Test marking task as downloading."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.mark_downloading()

        assert task.status == ExportTaskStatus.DOWNLOADING
        assert task.progress == 40.0

    def test_mark_exporting(self):
        """Test marking task as exporting."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.mark_exporting()

        assert task.status == ExportTaskStatus.EXPORTING
        assert task.progress == 70.0

    def test_mark_completed(self):
        """Test marking task as completed."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.mark_completed(
            output_path="/output/Test_Conversation",
            message_count=10,
            image_count=5
        )

        assert task.status == ExportTaskStatus.COMPLETED
        assert task.progress == 100.0
        assert task.output_path == "/output/Test_Conversation"
        assert task.message_count == 10
        assert task.image_count == 5
        assert task.completed_at is not None

    def test_mark_failed(self):
        """Test marking task as failed."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        task.mark_failed("Network error: connection timeout")

        assert task.status == ExportTaskStatus.FAILED
        assert task.error == "Network error: connection timeout"
        assert task.completed_at is not None

    def test_is_completed(self):
        """Test is_completed property."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        assert not task.is_completed

        task.mark_completed(output_path="/output")
        assert task.is_completed

    def test_is_failed(self):
        """Test is_failed property."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        assert not task.is_failed

        task.mark_failed("Error")
        assert task.is_failed

    def test_is_running(self):
        """Test is_running property."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        assert not task.is_running

        task.mark_parsing()
        assert task.is_running

        task.mark_downloading()
        assert task.is_running

        task.mark_exporting()
        assert task.is_running

        task.mark_completed(output_path="/output")
        assert not task.is_running

    def test_task_id_format(self):
        """Test task ID format."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        assert task.id.startswith("task_")
        assert len(task.id) == 17  # "task_" + 12 hex chars

    def test_created_at_default(self):
        """Test created_at is set by default."""
        before = datetime.now()
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        after = datetime.now()

        assert before <= task.created_at <= after