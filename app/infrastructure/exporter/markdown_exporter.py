"""Markdown exporter - exports KnowledgeDocument to Markdown files."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import structlog

from app.application.export_options import ExportOptions, MarkdownFormat
from app.config.settings import settings
from app.domain.model.block import Block, BlockType
from app.domain.model.knowledge_document import KnowledgeDocument
from app.domain.service.interfaces import ExporterInterface, ExportResult
from app.common.exceptions import ExportException
from app.common.utils import ensure_dir, sanitize_conversation_title, sanitize_filename

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
        include_images: bool = True,
        options: ExportOptions | None = None,
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
            options = options or ExportOptions()
            include_images = include_images and options.include_images

            # Create output directory
            title = sanitize_conversation_title(document.title)
            doc_dir = output_dir / title
            ensure_dir(doc_dir)

            # Create images directory if needed
            images_dir = doc_dir / settings.markdown_image_prefix
            if include_images and document.images:
                ensure_dir(images_dir)

            files_written: list[Path] = []

            # Build markdown content
            markdown_content = self._build_markdown(
                document,
                include_images,
                settings.markdown_image_prefix,
                options,
            )

            # Write markdown file
            basename = sanitize_filename(options.file_basename or "conversation")
            md_path = doc_dir / f"{basename}.md"
            md_path.write_text(markdown_content, encoding="utf-8")
            files_written.append(md_path)

            if options.create_index:
                index_path = doc_dir / "index.md"
                index_path.write_text(
                    self._build_index(document, basename, include_images, options),
                    encoding="utf-8",
                )
                files_written.append(index_path)

            if options.create_messages:
                messages_path = doc_dir / "messages.md"
                messages_path.write_text(
                    self._build_messages(document, include_images, settings.markdown_image_prefix),
                    encoding="utf-8",
                )
                files_written.append(messages_path)

            if options.create_manifest:
                manifest_path = doc_dir / "manifest.md"
                manifest_path.write_text(
                    self._build_manifest(document, files_written, include_images, options),
                    encoding="utf-8",
                )
                files_written.append(manifest_path)

            # Count actual files
            file_count = len(files_written)
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
        image_prefix: str,
        options: ExportOptions | None = None,
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
        options = options or ExportOptions()
        lines = []

        if options.include_frontmatter:
            lines.extend(self._frontmatter(document, "conversation", options))
            lines.append("")

        # Title
        lines.append(f"# {document.title}")
        lines.append("")

        # Metadata
        if options.include_metadata:
            lines.append(f"**Platform**: {document.platform.value}")
            lines.append(f"**Conversation ID**: {document.conversation_id}")
            source_url = document.metadata.get("source_url")
            if source_url:
                lines.append(f"**Source URL**: {source_url}")
            lines.append(f"**Exported**: {document.created_at.isoformat()}")
            lines.append(f"**Blocks**: {len(document.blocks)}")
            lines.append(f"**Images**: {len(document.images)}")
            lines.append("")

        # Separator
        lines.append("---")
        lines.append("")
        lines.append("## Conversation")
        lines.append("")

        # Process blocks in order
        for index, block in enumerate(document.blocks, start=1):
            if options.format == MarkdownFormat.AI_READABLE.value:
                role = block.metadata.get("role", "content").upper()
                lines.append(f"### Message {index}: {role}")
                lines.append("")
                lines.append(f"- block_id: `{block.id}`")
                lines.append(f"- block_type: `{block.block_type.value}`")
                lines.append("")
            md = self._format_block(block, include_images, image_prefix)
            if md:
                lines.append(md)
                lines.append("")

        return "\n".join(lines)

    def _frontmatter(
        self,
        document: KnowledgeDocument,
        document_type: str,
        options: ExportOptions,
    ) -> list[str]:
        """Build YAML frontmatter for markdown files."""
        source_url = str(document.metadata.get("source_url", ""))
        return [
            "---",
            f'title: "{self._yaml_escape(document.title)}"',
            f"document_type: {document_type}",
            f"platform: {document.platform.value}",
            f'conversation_id: "{self._yaml_escape(document.conversation_id)}"',
            f'conversation_url: "{self._yaml_escape(source_url)}"',
            f"export_format: {options.format}",
            f"block_count: {len(document.blocks)}",
            f"image_count: {len(document.images)}",
            f'created_at: "{document.created_at.isoformat()}"',
            "---",
        ]

    def _build_index(
        self,
        document: KnowledgeDocument,
        basename: str,
        include_images: bool,
        options: ExportOptions,
    ) -> str:
        """Build an index file optimized for agents and workflows."""
        lines = []
        if options.include_frontmatter:
            lines.extend(self._frontmatter(document, "index", options))
            lines.append("")
        lines.extend([
            f"# {document.title}",
            "",
            "## Files",
            "",
            f"- [{basename}.md](./{basename}.md): full conversation transcript",
        ])
        if options.create_messages:
            lines.append("- [messages.md](./messages.md): one message block per section")
        if options.create_manifest:
            lines.append("- [manifest.md](./manifest.md): export manifest and parser metadata")
        if include_images and document.images:
            lines.append(f"- `{settings.markdown_image_prefix}/`: downloaded image assets")
        lines.extend([
            "",
            "## Source",
            "",
            f"- platform: `{document.platform.value}`",
            f"- conversation_id: `{document.conversation_id}`",
        ])
        source_url = document.metadata.get("source_url")
        if source_url:
            lines.append(f"- url: {source_url}")
        lines.extend([
            "",
            "## Counts",
            "",
            f"- blocks: {len(document.blocks)}",
            f"- images: {len(document.images)}",
        ])
        return "\n".join(lines)

    def _build_messages(
        self,
        document: KnowledgeDocument,
        include_images: bool,
        image_prefix: str,
    ) -> str:
        """Build a message-by-message markdown file for retrieval systems."""
        lines = [f"# Messages - {document.title}", ""]
        for index, block in enumerate(document.blocks, start=1):
            role = block.metadata.get("role", "content")
            lines.extend([
                f"## Message {index}",
                "",
                f"- role: `{role}`",
                f"- block_id: `{block.id}`",
                f"- block_type: `{block.block_type.value}`",
                "",
            ])
            formatted = self._format_block(block, include_images, image_prefix)
            if formatted:
                lines.extend([formatted, ""])
        return "\n".join(lines)

    def _build_manifest(
        self,
        document: KnowledgeDocument,
        files_written: list[Path],
        include_images: bool,
        options: ExportOptions,
    ) -> str:
        """Build a markdown manifest with stable machine-readable fields."""
        lines = []
        if options.include_frontmatter:
            lines.extend(self._frontmatter(document, "manifest", options))
            lines.append("")
        lines.extend([
            f"# Manifest - {document.title}",
            "",
            "## Export",
            "",
            f"- format: `{options.format}`",
            f"- include_images: `{str(include_images).lower()}`",
            f"- include_metadata: `{str(options.include_metadata).lower()}`",
            "",
            "## Files",
            "",
        ])
        for path in files_written:
            lines.append(f"- `{path.name}`")
        if include_images and document.images:
            lines.extend(["", "## Images", ""])
            for image in document.images:
                local = image.local_filename or ""
                lines.append(f"- id: `{image.id}` url: {image.url} local: `{local}`")
        return "\n".join(lines)

    def _yaml_escape(self, value: str) -> str:
        """Escape a value for a simple quoted YAML scalar."""
        return value.replace("\\", "\\\\").replace('"', '\\"')

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
