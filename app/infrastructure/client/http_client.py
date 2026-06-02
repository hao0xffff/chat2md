"""HTTP client using aiohttp."""
import os
import aiohttp
from typing import Any

import structlog

from app.config.settings import settings
from app.common.exceptions import DownloadException

logger = structlog.get_logger()

# Default proxy URL - can be set via environment or hardcoded for development
DEFAULT_PROXY = "http://127.0.0.1:7890"


def _get_proxy() -> str | None:
    """Get proxy URL from environment."""
    for var in ["HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"]:
        proxy = os.environ.get(var)
        if proxy:
            return proxy
    return None

PROXY_URL = _get_proxy()


class HttpClient:
    """
    HTTP client wrapper around aiohttp.

    Provides a simple interface for making HTTP requests
    with connection pooling and timeout handling.
    Supports proxy via environment variables or default proxy.
    """

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        self._connector: aiohttp.TCPConnector | None = None
        self._logger = logger.bind(component="http_client")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=self._connector.limit if self._connector else settings.http_max_connections,
                limit_per_host=10,
                keepalive_timeout=settings.http_max_keepalive,
            )
            timeout = aiohttp.ClientTimeout(total=settings.http_timeout)
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
            )
        return self._session

    async def get(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """
        Make a GET request.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments for aiohttp request.

        Returns:
            The aiohttp response object.

        Raises:
            DownloadException: If the request fails.
        """
        session = await self._get_session()
        self._logger.debug("http_get", url=url)

        # Use proxy from env, default proxy, or kwargs
        proxy = kwargs.pop("proxy", PROXY_URL or DEFAULT_PROXY)

        try:
            response = await session.get(url, proxy=proxy, **kwargs)
            response.raise_for_status()
            return response
        except aiohttp.ClientError as e:
            self._logger.error("http_get_failed", url=url, error=str(e))
            raise DownloadException(
                message=f"Failed to fetch URL: {url}",
                resource_url=url,
            ) from e

    async def post(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """Make a POST request."""
        session = await self._get_session()
        self._logger.debug("http_post", url=url)
        try:
            response = await session.post(url, **kwargs)
            response.raise_for_status()
            return response
        except aiohttp.ClientError as e:
            self._logger.error("http_post_failed", url=url, error=str(e))
            raise DownloadException(
                message=f"Failed to post URL: {url}",
                resource_url=url,
            ) from e

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector and not self._connector.closed:
            await self._connector.close()

    async def __aenter__(self) -> "HttpClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()