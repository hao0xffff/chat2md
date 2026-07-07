"""File-backed export task repository."""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.application.export_task import ExportTask, ExportTaskStatus
from app.common.utils import ensure_dir


class FileTaskRepository:
    """Persist export tasks to a JSON file for restart-safe task lookup."""

    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        ensure_dir(self._path.parent)

    async def save(self, task: ExportTask) -> ExportTask:
        """Save or replace a task."""
        with self._lock:
            tasks = self._load_all()
            tasks[task.id] = self._task_to_dict(task)
            self._write_all(tasks)
        return task

    async def find_by_id(self, id: str) -> ExportTask | None:
        """Find a task by ID."""
        with self._lock:
            raw = self._load_all().get(id)
        return self._task_from_dict(raw) if raw else None

    async def update_status(
        self,
        id: str,
        status: ExportTaskStatus,
        **kwargs: Any,
    ) -> ExportTask | None:
        """Update task status and selected fields."""
        task = await self.find_by_id(id)
        if not task:
            return None
        task.status = status
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        await self.save(task)
        return task

    async def find_pending(self, limit: int = 10) -> list[ExportTask]:
        """Find pending tasks."""
        with self._lock:
            tasks = [self._task_from_dict(item) for item in self._load_all().values()]
        return [task for task in tasks if task.status == ExportTaskStatus.PENDING][:limit]

    def _load_all(self) -> dict[str, dict[str, Any]]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write_all(self, tasks: dict[str, dict[str, Any]]) -> None:
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(tasks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self._path)

    def _task_to_dict(self, task: ExportTask) -> dict[str, Any]:
        return {
            "id": task.id,
            "conversation_id": task.conversation_id,
            "url": task.url,
            "output_dir": task.output_dir,
            "export_options": task.export_options,
            "status": task.status.value,
            "progress": task.progress,
            "output_path": task.output_path,
            "error": task.error,
            "message_count": task.message_count,
            "image_count": task.image_count,
            "created_at": self._datetime_to_str(task.created_at),
            "updated_at": self._datetime_to_str(task.updated_at),
            "completed_at": self._datetime_to_str(task.completed_at),
        }

    def _task_from_dict(self, data: dict[str, Any]) -> ExportTask:
        return ExportTask(
            id=str(data["id"]),
            conversation_id=data.get("conversation_id"),
            url=data.get("url"),
            output_dir=data.get("output_dir"),
            export_options=data.get("export_options") or {},
            status=ExportTaskStatus(data.get("status", ExportTaskStatus.PENDING.value)),
            progress=float(data.get("progress", 0.0)),
            output_path=data.get("output_path"),
            error=data.get("error"),
            message_count=int(data.get("message_count", 0)),
            image_count=int(data.get("image_count", 0)),
            created_at=self._datetime_from_str(data.get("created_at")) or datetime.now(),
            updated_at=self._datetime_from_str(data.get("updated_at")) or datetime.now(),
            completed_at=self._datetime_from_str(data.get("completed_at")),
        )

    def _datetime_to_str(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    def _datetime_from_str(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
