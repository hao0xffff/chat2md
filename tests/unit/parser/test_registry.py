"""Unit tests for ParserRegistry."""
import pytest

from app.domain.parser.registry import ParserRegistry, register_parser
from app.domain.parser.interface import ConversationParser
from app.domain.value_objects import Platform
from app.common.exceptions import PlatformNotSupportedException
from app.domain.parser.base import BaseParser


class MockParser(BaseParser):
    """Mock parser for testing."""

    async def fetch(self, url: str) -> str:
        return ""

    def extract(self, html: str) -> dict:
        return {}

    def transform(self, data: dict):
        from app.domain.model.conversation import Conversation
        return Conversation(
            id="test",
            platform=Platform.CHATGPT,
            platform_conversation_id="test",
        )


class TestParserRegistry:
    """Tests for ParserRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        ParserRegistry._parsers.clear()

    def test_register(self):
        """Test parser registration."""
        ParserRegistry.register(Platform.CHATGPT, MockParser)
        assert ParserRegistry.is_registered(Platform.CHATGPT)

    def test_get_registered(self):
        """Test getting a registered parser."""
        ParserRegistry.register(Platform.CHATGPT, MockParser)
        parser_class = ParserRegistry.get(Platform.CHATGPT)
        assert parser_class == MockParser

    def test_get_unregistered(self):
        """Test getting an unregistered parser."""
        with pytest.raises(PlatformNotSupportedException):
            ParserRegistry.get(Platform.CHATGPT)

    def test_detect_platform_chatgpt(self):
        """Test platform detection - ChatGPT."""
        platform = ParserRegistry.detect_platform("https://chatgpt.com/share/abc123")
        assert platform == Platform.CHATGPT

    def test_detect_platform_gemini(self):
        """Test platform detection - Gemini."""
        platform = ParserRegistry.detect_platform("https://gemini.google.com/share/abc123")
        assert platform == Platform.GEMINI

    def test_detect_platform_gemini_share_domain(self):
        """Test platform detection - Gemini share.gemini.google links."""
        platform = ParserRegistry.detect_platform("https://share.gemini.google/Li9WOtl7kRLK")
        assert platform == Platform.GEMINI

    def test_detect_platform_doubao(self):
        """Test platform detection - Doubao."""
        platform = ParserRegistry.detect_platform("https://doubao.com/share/abc123")
        assert platform == Platform.DOUBAN

    def test_detect_platform_unsupported(self):
        """Test platform detection - unsupported."""
        with pytest.raises(PlatformNotSupportedException):
            ParserRegistry.detect_platform("https://unknown.com/share/abc123")

    def test_create_parser(self):
        """Test creating a parser instance."""
        ParserRegistry.register(Platform.CHATGPT, MockParser)
        parser = ParserRegistry.create_parser("https://chatgpt.com/share/abc123")
        assert isinstance(parser, MockParser)

    def test_decorator_registration(self):
        """Test the register_parser decorator."""
        @register_parser(Platform.GEMINI)
        class DecoratedParser(BaseParser):
            async def fetch(self, url: str) -> str:
                return ""

            def extract(self, html: str) -> dict:
                return {}

            def transform(self, data: dict):
                from app.domain.model.conversation import Conversation
                return Conversation(
                    id="test",
                    platform=Platform.GEMINI,
                    platform_conversation_id="test",
                )

        assert ParserRegistry.is_registered(Platform.GEMINI)

    def test_registered_platforms(self):
        """Test getting list of registered platforms."""
        ParserRegistry.register(Platform.CHATGPT, MockParser)
        ParserRegistry.register(Platform.GEMINI, MockParser)
        platforms = ParserRegistry.registered_platforms()
        assert Platform.CHATGPT.value in platforms
        assert Platform.GEMINI.value in platforms
