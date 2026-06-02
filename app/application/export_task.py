"""Export task model - tracks the status of export operations."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.common.utils import generate_task_id


class ExportTaskStatus(Enum):
    """Export task status enumeration."""
    PENDING = "pending"
    PARSING = "parsing"
    DOWNLOADING = "downloading"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExportTask:
    """
    Export Task - tracks the status of an export operation.

    This model lives in the Application layer and is used
    to track the progress of long-running export operations.
    """
    id: str = field(default_factory=generate_task_id)
    conversation_id: str | None = None
    url: str | None = None
    output_dir: str | None = None  # Custom output dir, None means use settings default
    status: ExportTaskStatus = ExportTaskStatus.PENDING
    progress: float = 0.0
    output_path: str | None = None
    error: str | None = None
    message_count: int = 0
    image_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def update_progress(self, progress: float, status: ExportTaskStatus | None = None) -> None:
        """Update task progress."""
        self.progress = min(max(progress, 0.0), 100.0)
        self.updated_at = datetime.now()
        if status:
            self.status = status

    def mark_parsing(self) -> None:
        """Mark task as parsing."""
        self.update_progress(10.0, ExportTaskStatus.PARSING)

    def mark_downloading(self) -> None:
        """Mark task as downloading."""
        self.update_progress(40.0, ExportTaskStatus.DOWNLOADING)

    def mark_exporting(self) -> None:
        """Mark task as exporting."""
        self.update_progress(70.0, ExportTaskStatus.EXPORTING)

    def mark_completed(
        self,
        output_path: str,
        message_count: int = 0,
        image_count: int = 0
    ) -> None:
        """Mark task as completed."""
        self.status = ExportTaskStatus.COMPLETED
        self.progress = 100.0
        self.output_path = output_path
        self.message_count = message_count
        self.image_count = image_count
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed."""
        self.status = ExportTaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == ExportTaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if task is failed."""
        return self.status == ExportTaskStatus.FAILED

    @property
    def is_running(self) -> bool:
        """Check if task is still running."""
        return self.status in {
            ExportTaskStatus.PARSING,
            ExportTaskStatus.DOWNLOADING,
            ExportTaskStatus.EXPORTING,
        }