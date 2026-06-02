"""Unit tests for Conversation model."""
import pytest
from datetime import datetime

from app.domain.model.conversation import Conversation
from app.domain.model.block import Block, BlockType
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform


class TestConversation:
    """Tests for Conversation model."""

    def test_creation(self):
        """Test basic conversation creation."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123"
        )
        assert conv.id == "conv_1"
        assert conv.platform == Platform.CHATGPT
        assert conv.platform_conversation_id == "chatgpt_123"
        assert conv.title is None
        assert conv.blocks == []
        assert conv.images == []

    def test_add_block(self):
        """Test adding blocks to conversation."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123"
        )
        block = Block(id="b1", block_type=BlockType.TEXT, content="Hello")
        conv.add_block(block)

        assert len(conv.blocks) == 1
        assert conv.blocks[0] == block

    def test_add_image(self):
        """Test adding images to conversation."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123"
        )
        img = ImageResource(id="img_1", url="https://example.com/image.png")
        conv.add_image(img)

        assert len(conv.images) == 1
        assert conv.images[0] == img

    def test_message_count(self):
        """Test message count property."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123"
        )
        conv.add_block(Block(id="b1", block_type=BlockType.TEXT, content="Text 1"))
        conv.add_block(Block(id="b2", block_type=BlockType.CODE, content="Code"))
        conv.add_block(Block(id="b3", block_type=BlockType.TEXT, content="Text 2"))

        assert conv.message_count == 3

    def test_title_default(self):
        """Test title default value."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123"
        )
        assert conv.title is None

    def test_created_at_default(self):
        """Test created_at default value."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123"
        )
        assert conv.created_at is None

    def test_metadata(self):
        """Test conversation metadata."""
        conv = Conversation(
            id="conv_1",
            platform=Platform.CHATGPT,
            platform_conversation_id="chatgpt_123",
            metadata={"source": "share_link", "version": "1.0"}
        )
        assert conv.metadata["source"] == "share_link"
        assert conv.metadata["version"] == "1.0"