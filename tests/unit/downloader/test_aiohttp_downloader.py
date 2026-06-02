"""Unit tests for AiohttpDownloader."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

from app.domain.model.image_resource import ImageResource
from app.infrastructure.downloader.aiohttp_downloader import AiohttpDownloader


class TestAiohttpDownloader:
    """Tests for AiohttpDownloader."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def sample_image(self):
        """Create a sample image resource."""
        return ImageResource(
            id="img_1",
            url="https://httpbin.org/image/png"
        )

    @pytest.mark.asyncio
    async def test_download_single_resource(self, temp_dir, sample_image):
        """Test downloading a single resource."""
        downloader = AiohttpDownloader()

        with patch.object(downloader, '_get_http_client') as mock_get_client:
            mock_response = AsyncMock()
            mock_response.read = AsyncMock(return_value=b"fake_image_data")
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_client = MagicMock()
            mock_client.get = MagicMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await downloader.download(sample_image, temp_dir)

            assert result.success
            assert result.local_path is not None
            assert (temp_dir / sample_image.filename).exists()

    @pytest.mark.asyncio
    async def test_download_batch(self, temp_dir):
        """Test batch downloading resources."""
        downloader = AiohttpDownloader()

        images = [
            ImageResource(id="img_1", url="https://httpbin.org/image/png"),
            ImageResource(id="img_2", url="https://httpbin.org/image/jpeg"),
        ]

        with patch.object(downloader, '_get_http_client') as mock_get_client:
            mock_response = AsyncMock()
            mock_response.read = AsyncMock(return_value=b"fake_data")
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_client = MagicMock()
            mock_client.get = MagicMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            results = await downloader.download_batch(images, temp_dir)

            assert len(results) == 2
            assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_download_with_progress_callback(self, temp_dir):
        """Test download with progress callback."""
        downloader = AiohttpDownloader()

        images = [
            ImageResource(id="img_1", url="https://httpbin.org/image/png"),
            ImageResource(id="img_2", url="https://httpbin.org/image/jpeg"),
        ]

        progress_updates = []

        def callback(current, total):
            progress_updates.append((current, total))

        with patch.object(downloader, '_get_http_client') as mock_get_client:
            mock_response = AsyncMock()
            mock_response.read = AsyncMock(return_value=b"fake_data")
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_client = MagicMock()
            mock_client.get = MagicMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await downloader.download_batch(images, temp_dir, progress_callback=callback)

            assert len(progress_updates) == 2
            assert progress_updates[0] == (1, 2)
            assert progress_updates[1] == (2, 2)

    @pytest.mark.asyncio
    async def test_download_empty_list(self, temp_dir):
        """Test downloading empty list."""
        downloader = AiohttpDownloader()
        results = await downloader.download_batch([], temp_dir)
        assert results == []

    def test_download_result_properties(self):
        """Test DownloadResult properties."""
        from app.domain.service.interfaces import DownloadResult

        result = DownloadResult(
            success=True,
            local_path=Path("/output/image.png"),
            file_size=1024,
            message="Downloaded successfully"
        )

        assert result.success is True
        assert result.local_path == Path("/output/image.png")
        assert result.file_size == 1024
        assert result.message == "Downloaded successfully"
        assert result.error is None