"""Unit tests for MarkdownExporter."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

from app.domain.model.block import Block, BlockType
from app.domain.model.image_resource import ImageResource
from app.domain.model.knowledge_document import KnowledgeDocument
from app.domain.value_objects import Platform
from app.infrastructure.exporter.markdown_exporter import MarkdownExporter


class TestMarkdownExporter:
    """Tests for MarkdownExporter."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def sample_document(self):
        """Create a sample knowledge document."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test Conversation",
            platform=Platform.CHATGPT,
            conversation_id="conv_123"
        )
        doc.add_block(Block(
            id="b1",
            block_type=BlockType.TEXT,
            content="Hello, how are you?",
            metadata={"role": "user"}
        ))
        doc.add_block(Block(
            id="b2",
            block_type=BlockType.TEXT,
            content="I'm doing great, thanks for asking!",
            metadata={"role": "assistant"}
        ))
        doc.add_block(Block(
            id="b3",
            block_type=BlockType.CODE,
            content="print('hello world')",
            language="python"
        ))
        doc.add_block(Block(
            id="b4",
            block_type=BlockType.TABLE,
            headers=["Name", "Age"],
            rows=[["Alice", "30"], ["Bob", "25"]]
        ))
        doc.add_block(Block(
            id="b5",
            block_type=BlockType.IMAGE,
            image_url="https://example.com/image.png",
            alt_text="Example Image"
        ))
        doc.add_block(Block(
            id="b6",
            block_type=BlockType.QUOTE,
            content="This is a famous quote",
            level=1
        ))
        doc.add_block(Block(
            id="b7",
            block_type=BlockType.LIST,
            items=["First item", "Second item", "Third item"]
        ))
        return doc

    @pytest.mark.asyncio
    async def test_export_document(self, temp_dir, sample_document):
        """Test exporting a document."""
        exporter = MarkdownExporter()
        result = await exporter.export(sample_document, temp_dir)

        assert result.success
        assert result.output_path is not None
        assert (result.output_path / "conversation.md").exists()

    @pytest.mark.asyncio
    async def test_export_creates_directory(self, temp_dir, sample_document):
        """Test that export creates proper directory structure."""
        exporter = MarkdownExporter()
        await exporter.export(sample_document, temp_dir)

        doc_dir = temp_dir / "Test_Conversation"
        assert doc_dir.exists()
        assert (doc_dir / "conversation.md").exists()
        assert (doc_dir / "images").exists()

    @pytest.mark.asyncio
    async def test_export_markdown_content(self, temp_dir, sample_document):
        """Test that markdown content is correct."""
        exporter = MarkdownExporter()
        await exporter.export(sample_document, temp_dir)

        md_path = temp_dir / "Test_Conversation" / "conversation.md"
        content = md_path.read_text()

        # Check title
        assert "# Test Conversation" in content

        # Check metadata
        assert "**Platform**: chatgpt" in content

        # Check blocks are present
        assert "Hello, how are you?" in content
        assert "print('hello world')" in content
        assert "```python" in content
        assert "| Name | Age |" in content
        assert "![Example Image]" in content
        assert "> This is a famous quote" in content
        assert "- First item" in content

    @pytest.mark.asyncio
    async def test_export_without_images(self, temp_dir, sample_document):
        """Test export without images."""
        exporter = MarkdownExporter()
        result = await exporter.export(sample_document, temp_dir, include_images=False)

        assert result.success
        # Images directory should not be created
        images_dir = temp_dir / "Test_Conversation" / "images"
        assert not images_dir.exists()

    @pytest.mark.asyncio
    async def test_export_batch(self, temp_dir):
        """Test batch export."""
        exporter = MarkdownExporter()

        doc1 = KnowledgeDocument(
            id="doc_1",
            title="Doc 1",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        doc1.add_block(Block(id="b1", block_type=BlockType.TEXT, content="Content 1"))

        doc2 = KnowledgeDocument(
            id="doc_2",
            title="Doc 2",
            platform=Platform.GEMINI,
            conversation_id="conv_2"
        )
        doc2.add_block(Block(id="b2", block_type=BlockType.TEXT, content="Content 2"))

        results = await exporter.export_batch([doc1, doc2], temp_dir)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert (temp_dir / "Doc_1" / "conversation.md").exists()
        assert (temp_dir / "Doc_2" / "conversation.md").exists()

    def test_format_text_block(self):
        """Test text block formatting."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.TEXT,
            content="Hello world",
            metadata={"role": "user"}
        )
        md = exporter._format_text_block(block)
        assert "**USER**" in md
        assert "Hello world" in md

    def test_format_code_block(self):
        """Test code block formatting."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.CODE,
            content="def hello():\n    return 'world'",
            language="python"
        )
        md = exporter._format_code_block(block)
        assert "```python" in md
        assert "def hello():" in md

    def test_format_table_block(self):
        """Test table block formatting."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.TABLE,
            headers=["A", "B"],
            rows=[["1", "2"], ["3", "4"]]
        )
        md = exporter._format_table_block(block)
        assert "| A | B |" in md
        assert "| --- | --- |" in md
        assert "| 1 | 2 |" in md

    def test_format_image_block(self):
        """Test image block formatting."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.IMAGE,
            image_url="https://example.com/img.png",
            alt_text="Test"
        )
        md = exporter._format_image_block(block, True, "images")
        assert "![Test](https://example.com/img.png)" in md

    def test_format_image_block_with_local_path(self):
        """Test image block with local path."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.IMAGE,
            image_url="https://example.com/img.png",
            alt_text="Test",
            metadata={"local_path": "images/image_1.png"}
        )
        md = exporter._format_image_block(block, True, "images")
        assert "![Test](images/image_1.png)" in md

    def test_format_quote_block(self):
        """Test quote block formatting."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.QUOTE,
            content="Quote text",
            level=1
        )
        md = exporter._format_quote_block(block)
        assert md == "> Quote text"

    def test_format_list_block(self):
        """Test list block formatting."""
        exporter = MarkdownExporter()
        block = Block(
            id="1",
            block_type=BlockType.LIST,
            items=["Item 1", "Item 2"]
        )
        md = exporter._format_list_block(block)
        assert "- Item 1" in md
        assert "- Item 2" in md