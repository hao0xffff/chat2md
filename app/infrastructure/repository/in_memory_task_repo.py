"""In-memory export task repository implementation."""
from app.application.export_task import ExportTask, ExportTaskStatus
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.domain.repository.interfaces import Repository


class InMemoryTaskRepository:
    """In-memory implementation for ExportTask storage."""

    def __init__(self):
        self._tasks: dict[str, ExportTask] = {}

    async def save(self, task: ExportTask) -> ExportTask:
        """Save a task."""
        self._tasks[task.id] = task
        return task

    async def find_by_id(self, id: str) -> ExportTask | None:
        """Find a task by ID."""
        return self._tasks.get(id)

    async def update_status(
        self,
        id: str,
        status: ExportTaskStatus,
        **kwargs
    ) -> ExportTask | None:
        """Update task status and additional fields."""
        task = self._tasks.get(id)
        if task:
            task.status = status
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
        return task

    async def find_pending(self, limit: int = 10) -> list[ExportTask]:
        """Find pending tasks."""
        return [
            task for task in self._tasks.values()
            if task.status == ExportTaskStatus.PENDING
        ][:limit]