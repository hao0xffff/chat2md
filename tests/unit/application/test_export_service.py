"""Unit tests for ExportService."""
from pathlib import Path

import pytest

from app.application.export_service import ExportService
from app.common.exceptions import ValidationException
from app.config.settings import settings


class TestExportServiceOutputDir:
    """Tests for output directory resolution."""

    def test_custom_output_dir_allowed_when_roots_empty(self, monkeypatch, tmp_path: Path):
        """Empty allowed roots means local custom paths are allowed."""
        monkeypatch.setattr(settings, "allowed_output_roots", [])
        service = ExportService(task_repository=None)

        resolved = service._resolve_output_dir(str(tmp_path), Path("output"))

        assert resolved == tmp_path.resolve()

    def test_custom_output_dir_restricted_when_roots_configured(
        self,
        monkeypatch,
        tmp_path: Path,
    ):
        """Configured roots restrict absolute custom paths."""
        allowed = tmp_path / "allowed"
        outside = tmp_path / "outside"
        monkeypatch.setattr(settings, "allowed_output_roots", [allowed])
        service = ExportService(task_repository=None)

        with pytest.raises(ValidationException):
            service._resolve_output_dir(str(outside), Path("output"))
