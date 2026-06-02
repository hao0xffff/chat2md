"""Markdown exporter - exports KnowledgeDocument to Markdown files."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import structlog

from app.config.settings import settings
from app.domain.model.block import Block, BlockType
from app.domain.model.knowledge_document import KnowledgeDocument
from app.domain.service.interfaces import ExporterInterface, ExportResult
from app.common.exceptions import ExportException
from app.common.utils import ensure_dir, sanitize_conversation_title

logger = structlog.get_logger()


class MarkdownExporter(ExporterInterface):
    """
    Markdown exporter - exports KnowledgeDocument to Markdown format.

    Creates a directory structure:
    output/
    └── conversation_title/
        ├── conversation.md
        └── images/
            ├── image1.png
            └── ...
    """

    def __init__(self):
        self._logger = logger.bind(component="exporter")

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
            output_dir: The base output directory.
            include_images: Whether to include image references.

        Returns:
            An ExportResult with the result of the operation.
        """
        try:
            # Create output directory
            title = sanitize_conversation_title(document.title)
            doc_dir = output_dir / title
            ensure_dir(doc_dir)

            # Create images directory if needed
            images_dir = doc_dir / settings.markdown_image_prefix
            if include_images and document.images:
                ensure_dir(images_dir)

            # Build markdown content
            markdown_content = self._build_markdown(document, include_images, settings.markdown_image_prefix)

            # Write markdown file
            md_path = doc_dir / "conversation.md"
            md_path.write_text(markdown_content, encoding="utf-8")

            # Count actual files
            file_count = 1  # The markdown file itself
            image_count = 0

            if include_images:
                for img in document.images:
                    if img.is_downloaded and img.local_path:
                        image_count += 1

            self._logger.info(
                "export_completed",
                output_dir=str(doc_dir),
                file_count=file_count,
                image_count=image_count
            )

            return ExportResult(
                success=True,
                output_path=doc_dir,
                file_count=file_count,
                image_count=image_count,
                message=f"Exported to {doc_dir}"
            )

        except Exception as e:
            self._logger.error("export_failed", error=str(e))
            return ExportResult(
                success=False,
                error=str(e),
                message=f"Export failed: {str(e)}"
            )

    async def export_batch(
        self,
        documents: list[KnowledgeDocument],
        output_dir: Path,
        include_images: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[ExportResult]:
        """
        Export multiple knowledge documents.

        Args:
            documents: List of KnowledgeDocument to export.
            output_dir: The base output directory.
            include_images: Whether to include image references.
            progress_callback: Optional callback(current, total) for progress.

        Returns:
            A list of ExportResult for each document.
        """
        results = []
        total = len(documents)

        for i, doc in enumerate(documents):
            result = await self.export(doc, output_dir, include_images)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def _build_markdown(
        self,
        document: KnowledgeDocument,
        include_images: bool,
        image_prefix: str
    ) -> str:
        """
        Build complete markdown content from a document.

        Args:
            document: The knowledge document.
            include_images: Whether to include images.
            image_prefix: The prefix for image paths.

        Returns:
            Markdown content as string.
        """
        lines = []

        # Title
        lines.append(f"# {document.title}")
        lines.append("")

        # Metadata
        lines.append(f"**Platform**: {document.platform.value}")
        lines.append(f"**Exported**: {document.created_at.isoformat()}")
        lines.append("")

        # Separator
        lines.append("---")
        lines.append("")

        # Process blocks in order
        for block in document.blocks:
            md = self._format_block(block, include_images, image_prefix)
            if md:
                lines.append(md)
                lines.append("")

        return "\n".join(lines)

    def _format_block(
        self,
        block: Block,
        include_images: bool,
        image_prefix: str
    ) -> str:
        """
        Format a single block to markdown.

        Args:
            block: The block to format.
            include_images: Whether to include images.
            image_prefix: The prefix for image paths.

        Returns:
            Markdown formatted string for the block.
        """
        if block.is_text:
            return self._format_text_block(block)
        elif block.is_code:
            return self._format_code_block(block)
        elif block.is_table:
            return self._format_table_block(block)
        elif block.is_image:
            return self._format_image_block(block, include_images, image_prefix)
        elif block.is_quote:
            return self._format_quote_block(block)
        elif block.is_list:
            return self._format_list_block(block)
        return ""

    def _format_text_block(self, block: Block) -> str:
        """Format a text block."""
        content = block.content or ""
        role = block.metadata.get("role", "user").upper()
        return f"**{role}**\n\n{content}"

    def _format_code_block(self, block: Block) -> str:
        """Format a code block with language identifier."""
        code = block.content or ""
        lang = block.language or ""
        fence = settings.markdown_code_fence
        return f"{fence}{lang}\n{code}\n{fence}"

    def _format_table_block(self, block: Block) -> str:
        """Format a table block as markdown table."""
        if not block.headers or not block.rows:
            return ""

        lines = []
        lines.append("| " + " | ".join(block.headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(block.headers)) + " |")
        for row in block.rows:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def _format_image_block(
        self,
        block: Block,
        include_images: bool,
        image_prefix: str
    ) -> str:
        """Format an image block."""
        if not block.image_url:
            return ""

        alt = block.alt_text or "image"
        url = block.image_url

        # If image is downloaded, reference the local file
        if include_images and block.metadata.get("local_path"):
            filename = block.metadata["local_path"].split("/")[-1].split("\\")[-1]
            url = f"{image_prefix}/{filename}"

        return f"![{alt}]({url})"

    def _format_quote_block(self, block: Block) -> str:
        """Format a quote block."""
        content = block.content or ""
        level = block.level or 1
        prefix = "> " * level
        return f"{prefix}{content}"

    def _format_list_block(self, block: Block) -> str:
        """Format a list block."""
        if not block.items:
            return ""
        return "\n".join([f"- {item}" for item in block.items])