"""Integration tests for export API."""
import pytest
import zipfile
from httpx import AsyncClient, ASGITransport

from app.api.routes import _build_export_archive
from app.main import app


class TestExportAPI:
    """Integration tests for export API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_export_invalid_url(self, client):
        """Test export with invalid URL."""
        response = await client.post(
            "/api/v1/export",
            json={"url": "https://example.com/invalid"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_export_missing_url(self, client):
        """Test export without URL."""
        response = await client.post("/api/v1/export", json={})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_batch_export(self, client):
        """Test batch export endpoint."""
        response = await client.post(
            "/api/v1/export/batch",
            json={"urls": [
                "https://example.com/share/1",
                "https://example.com/share/2"
            ]}
        )
        # May be 400 for invalid URLs, but should not crash
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client):
        """Test getting a task that doesn't exist."""
        response = await client.get("/api/v1/task/nonexistent_task_id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_nonexistent_task(self, client):
        """Test downloading a task that doesn't exist."""
        response = await client.get("/api/v1/download/nonexistent_task_id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_incomplete_task(self, client):
        """Test downloading an incomplete task."""
        # Create a task first
        export_response = await client.post(
            "/api/v1/export",
            json={"url": "https://chatgpt.com/share/abc123"}
        )
        if export_response.status_code == 200:
            task_id = export_response.json()["task_id"]
            response = await client.get(f"/api/v1/download/{task_id}")
            # Task should be incomplete, so 400
            assert response.status_code == 400

    def test_build_export_archive(self, tmp_path):
        """Directory exports are packaged as zip archives."""
        export_dir = tmp_path / "Conversation"
        export_dir.mkdir()
        (export_dir / "index.md").write_text("# Index", encoding="utf-8")
        nested = export_dir / "images"
        nested.mkdir()
        (nested / "image.png").write_bytes(b"image")

        archive_path = _build_export_archive("task_123", export_dir)

        assert archive_path.exists()
        with zipfile.ZipFile(archive_path) as archive:
            assert sorted(archive.namelist()) == ["images/image.png", "index.md"]
