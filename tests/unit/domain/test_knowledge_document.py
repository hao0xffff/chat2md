"""Unit tests for KnowledgeDocument model."""
import pytest
from datetime import datetime

from app.domain.model.block import Block, BlockType
from app.domain.model.image_resource import ImageResource
from app.domain.model.knowledge_document import KnowledgeDocument
from app.domain.value_objects import Platform


class TestKnowledgeDocument:
    """Tests for KnowledgeDocument model."""

    def test_document_creation(self):
        """Test basic document creation."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test Document",
            platform=Platform.CHATGPT,
            conversation_id="conv_123"
        )
        assert doc.id == "doc_1"
        assert doc.title == "Test Document"
        assert doc.platform == Platform.CHATGPT
        assert doc.conversation_id == "conv_123"
        assert doc.blocks == []
        assert doc.images == []

    def test_add_block(self):
        """Test adding blocks to document."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        block = Block(id="b1", block_type=BlockType.TEXT, content="Hello")
        doc.add_block(block)
        assert len(doc.blocks) == 1
        assert doc.blocks[0] == block

    def test_add_image(self):
        """Test adding images to document."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        img = ImageResource(id="img_1", url="https://example.com/image.png")
        doc.add_image(img)
        assert len(doc.images) == 1
        assert doc.images[0] == img

    def test_text_blocks_property(self):
        """Test text_blocks property."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        doc.add_block(Block(id="b1", block_type=BlockType.TEXT, content="Text 1"))
        doc.add_block(Block(id="b2", block_type=BlockType.CODE, content="Code"))
        doc.add_block(Block(id="b3", block_type=BlockType.TEXT, content="Text 2"))
        assert len(doc.text_blocks) == 2

    def test_code_blocks_property(self):
        """Test code_blocks property."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        doc.add_block(Block(id="b1", block_type=BlockType.TEXT, content="Text"))
        doc.add_block(Block(id="b2", block_type=BlockType.CODE, content="Code 1"))
        doc.add_block(Block(id="b3", block_type=BlockType.CODE, content="Code 2"))
        assert len(doc.code_blocks) == 2

    def test_image_blocks_property(self):
        """Test image_blocks property."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        doc.add_block(Block(id="b1", block_type=BlockType.TEXT, content="Text"))
        doc.add_block(Block(id="b2", block_type=BlockType.IMAGE, image_url="http://x.jpg"))
        assert len(doc.image_blocks) == 1

    def test_all_markdown(self):
        """Test all_markdown property."""
        doc = KnowledgeDocument(
            id="doc_1",
            title="Test",
            platform=Platform.CHATGPT,
            conversation_id="conv_1"
        )
        doc.add_block(Block(id="b1", block_type=BlockType.TEXT, content="Hello"))
        doc.add_block(Block(id="b2", block_type=BlockType.TEXT, content="World"))
        md = doc.all_markdown
        assert "Hello" in md
        assert "World" in md