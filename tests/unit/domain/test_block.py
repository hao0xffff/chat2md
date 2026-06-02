"""Unit tests for Block model."""
import pytest

from app.domain.model.block import Block, BlockType


class TestBlock:
    """Tests for Block model."""

    def test_block_creation(self):
        """Test basic block creation."""
        block = Block(
            id="block_1",
            block_type=BlockType.TEXT,
            content="Hello, world!"
        )
        assert block.id == "block_1"
        assert block.block_type == BlockType.TEXT
        assert block.content == "Hello, world!"
        assert block.metadata == {}

    def test_block_type_properties(self):
        """Test block type property checks."""
        block = Block(id="1", block_type=BlockType.TEXT)
        assert block.is_text
        assert not block.is_code

        block = Block(id="2", block_type=BlockType.CODE)
        assert block.is_code
        assert not block.is_text

        block = Block(id="3", block_type=BlockType.TABLE)
        assert block.is_table

        block = Block(id="4", block_type=BlockType.IMAGE)
        assert block.is_image

        block = Block(id="5", block_type=BlockType.QUOTE)
        assert block.is_quote

        block = Block(id="6", block_type=BlockType.LIST)
        assert block.is_list

    def test_text_block_to_markdown(self):
        """Test text block markdown conversion."""
        block = Block(
            id="1",
            block_type=BlockType.TEXT,
            content="This is a text block"
        )
        assert block.to_markdown() == "This is a text block"

    def test_code_block_to_markdown(self):
        """Test code block markdown conversion."""
        block = Block(
            id="1",
            block_type=BlockType.CODE,
            content="print('hello')",
            language="python"
        )
        expected = "```python\nprint('hello')\n```"
        assert block.to_markdown() == expected

    def test_code_block_without_language(self):
        """Test code block without language."""
        block = Block(
            id="1",
            block_type=BlockType.CODE,
            content="some code"
        )
        expected = "```\nsome code\n```"
        assert block.to_markdown() == expected

    def test_table_block_to_markdown(self):
        """Test table block markdown conversion."""
        block = Block(
            id="1",
            block_type=BlockType.TABLE,
            headers=["Name", "Age"],
            rows=[["Alice", "30"], ["Bob", "25"]]
        )
        md = block.to_markdown()
        assert "| Name | Age |" in md
        assert "| --- | --- |" in md
        assert "| Alice | 30 |" in md
        assert "| Bob | 25 |" in md

    def test_table_block_empty(self):
        """Test table block with no data."""
        block = Block(id="1", block_type=BlockType.TABLE)
        assert block.to_markdown() == ""

    def test_image_block_to_markdown(self):
        """Test image block markdown conversion."""
        block = Block(
            id="1",
            block_type=BlockType.IMAGE,
            image_url="https://example.com/image.png",
            alt_text="Example"
        )
        assert block.to_markdown() == "![Example](https://example.com/image.png)"

    def test_image_block_without_alt(self):
        """Test image block without alt text."""
        block = Block(
            id="1",
            block_type=BlockType.IMAGE,
            image_url="https://example.com/image.png"
        )
        assert block.to_markdown() == "![image](https://example.com/image.png)"

    def test_quote_block_to_markdown(self):
        """Test quote block markdown conversion."""
        block = Block(
            id="1",
            block_type=BlockType.QUOTE,
            content="This is a quote",
            level=1
        )
        assert block.to_markdown() == "> This is a quote"

    def test_quote_block_nested(self):
        """Test nested quote block."""
        block = Block(
            id="1",
            block_type=BlockType.QUOTE,
            content="Nested quote",
            level=2
        )
        assert block.to_markdown() == "> > Nested quote"

    def test_list_block_to_markdown(self):
        """Test list block markdown conversion."""
        block = Block(
            id="1",
            block_type=BlockType.LIST,
            items=["item 1", "item 2", "item 3"]
        )
        md = block.to_markdown()
        assert "- item 1" in md
        assert "- item 2" in md
        assert "- item 3" in md

    def test_list_block_empty(self):
        """Test list block with no items."""
        block = Block(id="1", block_type=BlockType.LIST)
        assert block.to_markdown() == ""

    def test_block_with_metadata(self):
        """Test block with metadata."""
        block = Block(
            id="1",
            block_type=BlockType.TEXT,
            content="Test",
            metadata={"role": "user", "message_id": "msg_123"}
        )
        assert block.metadata["role"] == "user"
        assert block.metadata["message_id"] == "msg_123"