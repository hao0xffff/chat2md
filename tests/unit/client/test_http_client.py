"""Unit tests for HttpClient."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.client.http_client import HttpClient


class TestHttpClient:
    """Tests for HttpClient."""

    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request."""
        client = HttpClient()

        with patch.object(client, '_get_session') as mock_get_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.closed = False
            mock_get_session.return_value = mock_session

            response = await client.get("https://example.com/api")

            mock_session.get.assert_called_once()
            assert response == mock_response

    @pytest.mark.asyncio
    async def test_get_request_failure(self):
        """Test GET request failure."""
        import aiohttp
        client = HttpClient()

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))
            mock_session.closed = False
            mock_get_session.return_value = mock_session

            from app.common.exceptions import DownloadException
            with pytest.raises(DownloadException):
                await client.get("https://example.com/api")

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request."""
        client = HttpClient()

        with patch.object(client, '_get_session') as mock_get_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_response)
            mock_session.closed = False
            mock_get_session.return_value = mock_session

            response = await client.post("https://example.com/api", json={"key": "value"})

            mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        client = HttpClient()

        with patch.object(client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session.close = AsyncMock()
            mock_get_session.return_value = mock_session

            client._session = mock_session
            await client.close()

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using client as context manager."""
        async with HttpClient() as client:
            assert client is not None