"""Unit tests for BaseParser."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.parser.base import BaseParser
from app.domain.model.conversation import Conversation
from app.domain.value_objects import Platform
from app.common.exceptions import ParserException


class ConcreteParser(BaseParser):
    """Concrete implementation of BaseParser for testing."""

    async def fetch(self, url: str) -> str:
        return "<html>Test</html>"

    def extract(self, html: str) -> dict:
        return {"title": "Test", "id": "conv_123", "messages": []}

    def transform(self, data: dict) -> Conversation:
        return Conversation(
            id=data["id"],
            platform=Platform.CHATGPT,
            platform_conversation_id=data["id"],
            title=data.get("title", "Untitled"),
        )


class TestBaseParser:
    """Tests for BaseParser template method."""

    def test_detect_platform_chatgpt(self):
        """Test platform detection for ChatGPT."""
        parser = ConcreteParser()
        platform = parser._detect_platform("https://chatgpt.com/share/abc123")
        assert platform == Platform.CHATGPT

    def test_detect_platform_gemini(self):
        """Test platform detection for Gemini."""
        parser = ConcreteParser()
        platform = parser._detect_platform("https://gemini.google.com/share/abc123")
        assert platform == Platform.GEMINI

    def test_detect_platform_doubao(self):
        """Test platform detection for Doubao."""
        parser = ConcreteParser()
        platform = parser._detect_platform("https://doubao.com/share/abc123")
        assert platform == Platform.DOUBAN

    def test_detect_platform_unsupported(self):
        """Test platform detection for unsupported URL."""
        parser = ConcreteParser()
        with pytest.raises(ValueError):
            parser._detect_platform("https://unknown.com/share/abc123")

    def test_sanitize_title(self):
        """Test title sanitization."""
        parser = ConcreteParser()
        assert parser._sanitize_title("Normal Title") == "Normal Title"
        assert parser._sanitize_title("Title with | special") == "Title with  special"
        assert parser._sanitize_title("  Spaces  ") == "Spaces"
        assert parser._sanitize_title("Title<>:/\\?*") == "Title"

    @pytest.mark.asyncio
    async def test_parse_success(self):
        """Test successful parsing."""
        parser = ConcreteParser()
        result = await parser.parse("https://chatgpt.com/share/abc123")
        assert isinstance(result, Conversation)
        assert result.title == "Test"

    @pytest.mark.asyncio
    async def test_parse_failure(self):
        """Test parsing failure."""
        class FailingParser(ConcreteParser):
            async def fetch(self, url: str) -> str:
                raise Exception("Network error")

        parser = FailingParser()
        with pytest.raises(ParserException):
            await parser.parse("https://chatgpt.com/share/abc123")