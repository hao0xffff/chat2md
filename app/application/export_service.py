"""Export service - orchestrates the export workflow."""
from pathlib import Path
from typing import Any

import structlog

from app.application.export_options import ExportOptions
from app.application.export_task import ExportTask, ExportTaskStatus
from app.config.settings import settings
from app.domain.model.conversation import Conversation
from app.domain.model.knowledge_document import KnowledgeDocument
from app.domain.parser.registry import ParserRegistry
from app.domain.service.interfaces import DownloaderInterface, ExporterInterface
from app.common.utils import sanitize_conversation_title

logger = structlog.get_logger()


class ExportService:
    """
    Export service - orchestrates the complete export workflow.

    Coordinates:
    1. URL parsing (selecting correct parser)
    2. HTML fetching
    3. Data extraction
    4. Image downloading
    5. Markdown export
    """

    def __init__(
        self,
        parser_registry: type[ParserRegistry] = ParserRegistry,
        exporter: ExporterInterface | None = None,
        downloader: DownloaderInterface | None = None,
        task_repository: "InMemoryTaskRepository | None" = None,
    ):
        import app.infrastructure.parser  # noqa: F401

        self._parser_registry = parser_registry
        self._exporter = exporter or self._default_exporter()
        self._downloader = downloader or self._default_downloader()
        self._task_repo = task_repository
        self._logger = logger.bind(component="export_service")

    def _default_exporter(self) -> ExporterInterface:
        """Create default markdown exporter."""
        from app.infrastructure.exporter.markdown_exporter import MarkdownExporter
        return MarkdownExporter()

    def _default_downloader(self) -> DownloaderInterface:
        """Create default downloader."""
        from app.infrastructure.downloader.aiohttp_downloader import AiohttpDownloader
        return AiohttpDownloader()

    async def create_export_task(
        self,
        url: str,
        output_dir: str | None = None,
        export_options: dict[str, Any] | ExportOptions | None = None,
    ) -> ExportTask:
        """Create an export task."""
        platform = self._parser_registry.detect_platform(url)
        self._parser_registry.get(platform)
        options = (
            export_options
            if isinstance(export_options, ExportOptions)
            else ExportOptions.from_mapping(export_options)
        )
        task = ExportTask(url=url, output_dir=output_dir, export_options=options.to_dict())
        if self._task_repo:
            await self._task_repo.save(task)
        return task

    async def execute_export(self, task_id: str) -> ExportTask:
        """
        Execute the full export workflow.

        Args:
            task_id: The ID of the task to execute.

        Returns:
            The completed ExportTask.
        """
        if not self._task_repo:
            raise RuntimeError("Task repository not configured")

        task = await self._task_repo.find_by_id(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        try:
            task.mark_parsing()
            await self._task_repo.save(task)

            options = ExportOptions.from_mapping(task.export_options)

            # Parse the URL
            parser = ParserRegistry.create_parser(task.url)
            conversation = await parser.parse(task.url)
            task.conversation_id = conversation.id
            conversation.metadata["source_url"] = task.url
            conversation.metadata["export_options"] = options.to_dict()

            # Determine output directory
            default_output_dir = settings.local_output_dir or settings.output_dir
            if settings.allow_custom_output_dir and task.output_dir:
                base_output_dir = Path(task.output_dir)
            else:
                base_output_dir = default_output_dir

            # Mark images for download
            images = list(conversation.images)
            if images and options.include_images:
                task.mark_downloading()
                await self._task_repo.save(task)

                # Download images
                output_dir = base_output_dir / sanitize_conversation_title(conversation.title)
                image_results = await self._downloader.download_batch(
                    images,
                    output_dir / settings.markdown_image_prefix
                )

                # Update image local paths and wire to blocks
                image_id_to_resource = {img.id: img for img in images}
                for i, result in enumerate(image_results):
                    if i < len(images) and result.success and result.local_path:
                        images[i].mark_downloaded(str(result.local_path))

                for block in conversation.blocks:
                    if block.is_image:
                        image_id = block.metadata.get("image_id")
                        if image_id and image_id in image_id_to_resource:
                            img = image_id_to_resource[image_id]
                            block.metadata["local_path"] = img.local_path or ""
                            block.metadata["local_filename"] = img.local_filename or ""

            # Export to markdown
            task.mark_exporting()
            await self._task_repo.save(task)

            document = self._conversation_to_document(conversation)
            export_result = await self._exporter.export(
                document,
                base_output_dir,
                include_images=options.include_images,
                options=options,
            )

            if export_result.success:
                task.mark_completed(
                    output_path=str(export_result.output_path),
                    message_count=len(conversation.blocks),
                    image_count=len(images)
                )
            else:
                task.mark_failed(export_result.error or "Export failed")

            await self._task_repo.save(task)
            return task

        except Exception as e:
            self._logger.error("export_failed", task_id=task_id, error=str(e))
            task.mark_failed(str(e))
            if self._task_repo:
                await self._task_repo.save(task)
            return task

    def _conversation_to_document(self, conversation: Conversation) -> KnowledgeDocument:
        """Convert a Conversation to a KnowledgeDocument."""
        return KnowledgeDocument(
            id=conversation.id,
            title=conversation.title or "Untitled",
            platform=conversation.platform,
            conversation_id=conversation.id,
            blocks=list(conversation.blocks),
            images=list(conversation.images),
            metadata={
                **conversation.metadata,
                "message_count": len(conversation.blocks),
                "image_count": len(conversation.images),
            },
        )
