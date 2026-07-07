"""Tests for the file-backed task repository."""
from pathlib import Path

import pytest

from app.application.export_task import ExportTask, ExportTaskStatus
from app.infrastructure.repository.file_task_repo import FileTaskRepository


class TestFileTaskRepository:
    """Tests for FileTaskRepository."""

    @pytest.mark.asyncio
    async def test_save_and_reload_task(self, tmp_path: Path):
        """Saved tasks can be loaded by a new repository instance."""
        repo_path = tmp_path / "tasks.json"
        repo = FileTaskRepository(repo_path)
        task = ExportTask(url="https://chatgpt.com/share/abc")
        task.mark_completed(output_path=str(tmp_path / "export"), message_count=3, image_count=1)

        await repo.save(task)

        reloaded_repo = FileTaskRepository(repo_path)
        found = await reloaded_repo.find_by_id(task.id)

        assert found is not None
        assert found.id == task.id
        assert found.status == ExportTaskStatus.COMPLETED
        assert found.message_count == 3
        assert found.image_count == 1

    @pytest.mark.asyncio
    async def test_find_pending_limit(self, tmp_path: Path):
        """Pending lookup works across persisted tasks."""
        repo = FileTaskRepository(tmp_path / "tasks.json")
        for index in range(3):
            await repo.save(ExportTask(url=f"https://chatgpt.com/share/{index}"))
        completed = ExportTask(url="https://chatgpt.com/share/done")
        completed.mark_completed(output_path=str(tmp_path / "done"))
        await repo.save(completed)

        pending = await repo.find_pending(limit=2)

        assert len(pending) == 2
        assert all(task.status == ExportTaskStatus.PENDING for task in pending)
