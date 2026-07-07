"""Image downloader with concurrent download support."""
from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from typing import Callable, Optional

import aiofiles
import structlog

from app.config.settings import settings
from app.domain.model.image_resource import ImageResource
from app.domain.service.interfaces import DownloaderInterface, DownloadResult
from app.common.exceptions import DownloadException
from app.common.utils import ensure_dir

logger = structlog.get_logger()


class AiohttpDownloader(DownloaderInterface):
    """
    Image resource downloader using aiohttp.

    Supports concurrent downloads and progress reporting.
    """

    def __init__(self, http_client=None):
        self._http_client = http_client
        self._logger = logger.bind(component="downloader")

    async def _get_http_client(self):
        """Lazy-load HTTP client to avoid circular imports."""
        if self._http_client is None:
            from app.infrastructure.client.http_client import HttpClient
            self._http_client = HttpClient()
        return self._http_client

    async def download(
        self,
        resource: ImageResource,
        output_dir: Path,
        overwrite: bool = False
    ) -> DownloadResult:
        """
        Download a single resource.

        Args:
            resource: The ImageResource to download.
            output_dir: The directory to save the resource.
            overwrite: Whether to overwrite existing files.

        Returns:
            A DownloadResult with the result.
        """
        output_path = output_dir / resource.filename

        if output_path.exists() and not overwrite:
            self._logger.info("file_already_exists", path=str(output_path))
            resource.mark_downloaded(str(output_path))
            return DownloadResult(
                success=True,
                local_path=output_path,
                message=f"File already exists: {resource.filename}"
            )

        try:
            client = await self._get_http_client()
            request = client.get(resource.url)
            response = await request if inspect.isawaitable(request) else request

            read_result = response.read()
            content = await read_result if inspect.isawaitable(read_result) else read_result
            file_size = len(content)

            if file_size > settings.max_file_size:
                raise DownloadException(
                    message=f"File too large: {file_size} bytes (max: {settings.max_file_size})",
                    resource_url=resource.url,
                )

            ensure_dir(output_dir)
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(content)

            resource.mark_downloaded(str(output_path))
            resource.file_size = file_size

            self._logger.info(
                "download_completed",
                url=resource.url,
                path=str(output_path),
                size=file_size
            )

            return DownloadResult(
                success=True,
                local_path=output_path,
                file_size=file_size,
                message=f"Downloaded: {resource.filename}"
            )

        except Exception as e:
            self._logger.error(
                "download_failed",
                url=resource.url,
                error=str(e)
            )
            return DownloadResult(
                success=False,
                error=str(e),
                message=f"Failed to download: {resource.url}"
            )

    async def download_batch(
        self,
        resources: list[ImageResource],
        output_dir: Path,
        overwrite: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[DownloadResult]:
        """
        Download multiple resources concurrently.

        Uses asyncio.gather with semaphore to limit concurrent downloads.

        Args:
            resources: List of ImageResource to download.
            output_dir: The directory to save the resources.
            overwrite: Whether to overwrite existing files.
            progress_callback: Optional callback(current, total) for progress.

        Returns:
            A list of DownloadResult for each resource.
        """
        if not resources:
            return []

        self._logger.info(
            "batch_download_started",
            total=len(resources),
            max_concurrent=settings.max_concurrent_downloads
        )

        semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        results: list[DownloadResult] = []
        completed = 0

        async def download_with_semaphore(resource: ImageResource) -> DownloadResult:
            nonlocal completed
            async with semaphore:
                result = await self.download(resource, output_dir, overwrite)
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(resources))
                return result

        tasks = [download_with_semaphore(r) for r in resources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results: list[DownloadResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(DownloadResult(
                    success=False,
                    error=str(result),
                    message=f"Download failed: {resources[i].url}"
                ))
            else:
                final_results.append(result)

        successful = sum(1 for r in final_results if r.success)
        self._logger.info(
            "batch_download_completed",
            total=len(resources),
            successful=successful,
            failed=len(resources) - successful
        )

        return final_results
