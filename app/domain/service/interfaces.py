"""Domain service interfaces - define service contracts."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.domain.model.image_resource import ImageResource
from app.domain.model.knowledge_document import KnowledgeDocument


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    output_path: Path | None = None
    file_count: int = 0
    image_count: int = 0
    message: str = ""
    error: str | None = None


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    local_path: Path | None = None
    file_size: int = 0
    message: str = ""
    error: str | None = None


class DownloaderInterface(ABC):
    """Interface for resource downloader."""

    @abstractmethod
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
            A DownloadResult with the result of the operation.
        """
        pass

    @abstractmethod
    async def download_batch(
        self,
        resources: list[ImageResource],
        output_dir: Path,
        overwrite: bool = False,
        progress_callback: callable | None = None
    ) -> list[DownloadResult]:
        """
        Download multiple resources concurrently.

        Args:
            resources: List of ImageResource to download.
            output_dir: The directory to save the resources.
            overwrite: Whether to overwrite existing files.
            progress_callback: Optional callback(current, total) for progress updates.

        Returns:
            A list of DownloadResult for each resource.
        """
        pass


class ExporterInterface(ABC):
    """Interface for document exporter."""

    @abstractmethod
    async def export(
        self,
        document: KnowledgeDocument,
        output_dir: Path,
        include_images: bool = True
    ) -> ExportResult:
        """
        Export a knowledge document to markdown.

        Args:
            document: The KnowledgeDocument to export.
            output_dir: The directory to export to.
            include_images: Whether to include image references.

        Returns:
            An ExportResult with the result of the operation.
        """
        pass

    @abstractmethod
    async def export_batch(
        self,
        documents: list[KnowledgeDocument],
        output_dir: Path,
        include_images: bool = True,
        progress_callback: callable | None = None
    ) -> list[ExportResult]:
        """
        Export multiple knowledge documents.

        Args:
            documents: List of KnowledgeDocument to export.
            output_dir: The directory to export to.
            include_images: Whether to include image references.
            progress_callback: Optional callback(current, total) for progress updates.

        Returns:
            A list of ExportResult for each document.
        """
        pass