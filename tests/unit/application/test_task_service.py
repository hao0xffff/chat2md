"""Unit tests for TaskService."""
import pytest

from app.application.export_task import ExportTask, ExportTaskStatus
from app.application.task_service import TaskService, InMemoryTaskRepository
from app.common.exceptions import TaskNotFoundException


class TestTaskService:
    """Tests for TaskService."""

    @pytest.fixture
    def service(self):
        """Create a task service with fresh repository."""
        repo = InMemoryTaskRepository()
        return TaskService(task_repository=repo)

    @pytest.mark.asyncio
    async def test_create_task(self, service):
        """Test creating a task."""
        task = await service.create_task("https://chatgpt.com/share/abc123")
        assert task.id is not None
        assert task.url == "https://chatgpt.com/share/abc123"
        assert task.status == ExportTaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_task(self, service):
        """Test getting a task by ID."""
        created = await service.create_task("https://chatgpt.com/share/abc123")
        retrieved = await service.get_task(created.id)
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, service):
        """Test getting a non-existent task."""
        with pytest.raises(TaskNotFoundException):
            await service.get_task("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_task_status(self, service):
        """Test getting task status."""
        task = await service.create_task("https://chatgpt.com/share/abc123")
        status = await service.get_task_status(task.id)
        assert status.task_id == task.id
        assert status.status == "pending"

    @pytest.mark.asyncio
    async def test_get_task_status_completed(self, service):
        """Test getting status of completed task."""
        task = await service.create_task("https://chatgpt.com/share/abc123")
        task.mark_completed(output_path="/output/test", message_count=5, image_count=2)
        await service._task_repo.save(task)

        status = await service.get_task_status(task.id)
        assert status.status == "completed"
        assert status.progress == 100.0
        assert status.message_count == 5
        assert status.image_count == 2


class TestInMemoryTaskRepository:
    """Tests for InMemoryTaskRepository."""

    @pytest.fixture
    def repo(self):
        """Create a fresh repository."""
        return InMemoryTaskRepository()

    @pytest.mark.asyncio
    async def test_save_and_find(self, repo):
        """Test saving and finding a task."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        await repo.save(task)

        found = await repo.find_by_id(task.id)
        assert found is not None
        assert found.id == task.id

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repo):
        """Test finding by ID when not exists."""
        found = await repo.find_by_id("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_status(self, repo):
        """Test updating task status."""
        task = ExportTask(url="https://chatgpt.com/share/abc123")
        await repo.save(task)

        await repo.update_status(task.id, ExportTaskStatus.PARSING)
        found = await repo.find_by_id(task.id)
        assert found.status == ExportTaskStatus.PARSING

    @pytest.mark.asyncio
    async def test_find_pending(self, repo):
        """Test finding pending tasks."""
        task1 = ExportTask(url="https://chatgpt.com/share/1")
        task2 = ExportTask(url="https://chatgpt.com/share/2")
        task3 = ExportTask(url="https://chatgpt.com/share/3")
        task3.mark_completed(output_path="/output")

        await repo.save(task1)
        await repo.save(task2)
        await repo.save(task3)

        pending = await repo.find_pending()
        assert len(pending) == 2
        assert all(t.status == ExportTaskStatus.PENDING for t in pending)

    @pytest.mark.asyncio
    async def test_find_pending_limit(self, repo):
        """Test pending tasks limit."""
        for i in range(15):
            task = ExportTask(url=f"https://chatgpt.com/share/{i}")
            await repo.save(task)

        pending = await repo.find_pending(limit=10)
        assert len(pending) == 10