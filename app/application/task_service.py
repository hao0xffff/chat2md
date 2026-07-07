"""Task service - manages export tasks."""
import structlog

from app.application.export_task import ExportTask, ExportTaskStatus
from app.application.dto import TaskStatusResponse
from app.common.exceptions import TaskNotFoundException

logger = structlog.get_logger()


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


class TaskService:
    """Service for managing export tasks."""

    def __init__(self, task_repository: InMemoryTaskRepository | None = None):
        self._task_repo = task_repository or InMemoryTaskRepository()
        self._logger = logger.bind(component="task_service")

    async def get_task(self, task_id: str) -> ExportTask:
        """
        Get a task by ID.

        Args:
            task_id: The task ID.

        Returns:
            The ExportTask.

        Raises:
            TaskNotFoundException: If task not found.
        """
        task = await self._task_repo.find_by_id(task_id)
        if not task:
            raise TaskNotFoundException(task_id)
        return task

    async def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """
        Get the status of a task.

        Args:
            task_id: The task ID.

        Returns:
            A TaskStatusResponse DTO.
        """
        task = await self.get_task(task_id)
        return TaskStatusResponse(
            task_id=task.id,
            status=task.status.value,
            progress=task.progress,
            url=task.url,
            output_path=task.output_path,
            error=task.error,
            message_count=task.message_count,
            image_count=task.image_count,
            export_options=task.export_options,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )

    async def create_task(self, url: str) -> ExportTask:
        """Create a new export task."""
        task = ExportTask(url=url)
        await self._task_repo.save(task)
        self._logger.info("task_created", task_id=task.id, url=url)
        return task
