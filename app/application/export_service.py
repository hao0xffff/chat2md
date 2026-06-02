"""Export service - orchestrates the export workflow."""
from pathlib import Path

import structlog

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

    async def create_export_task(self, url: str) -> ExportTask:
        """Create an export task."""
        task = ExportTask(url=url)
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

            # Parse the URL
            parser = ParserRegistry.create_parser(task.url)
            conversation = await parser.parse(task.url)
            task.conversation_id = conversation.id

            # Mark images for download
            images = list(conversation.images)
            if images:
                task.mark_downloading()
                await self._task_repo.save(task)

                # Download images
                output_dir = settings.output_dir / sanitize_conversation_title(conversation.title)
                image_results = await self._downloader.download_batch(
                    images,
                    output_dir / settings.markdown_image_prefix
                )

                # Update image local paths and wire to blocks
                image_id_to_resource = {img.id: img for img in images}
                for block in conversation.blocks:
                    if block.is_image:
                        image_id = block.metadata.get("image_id")
                        if image_id and image_id in image_id_to_resource:
                            img = image_id_to_resource[image_id]
                            if result.success and result.local_path:
                                img.mark_downloaded(str(result.local_path))
                            block.metadata["local_path"] = img.local_path or ""
                            block.metadata["local_filename"] = img.local_filename or ""

            # Export to markdown
            task.mark_exporting()
            await self._task_repo.save(task)

            document = self._conversation_to_document(conversation)
            export_result = await self._exporter.export(document, settings.output_dir)

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
            metadata=conversation.metadata,
        )