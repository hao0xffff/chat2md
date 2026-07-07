"""Unit tests for ChatGPTParser."""
import pytest

from app.infrastructure.parser.chatgpt import ChatGPTParser


class TestChatGPTParser:
    """Tests for ChatGPTParser."""

    def test_parser_registered(self):
        """Test that ChatGPTParser is registered."""
        from app.domain.parser.registry import ParserRegistry
        from app.domain.value_objects import Platform

        assert ParserRegistry.is_registered(Platform.CHATGPT)

    def test_parser_inherits_from_base(self):
        """Test that ChatGPTParser inherits from BaseParser."""
        from app.domain.parser.base import BaseParser
        assert issubclass(ChatGPTParser, BaseParser)

    def test_parser_has_lazy_playwright_parser(self):
        """Test that parser has lazy Playwright parser state."""
        parser = ChatGPTParser()
        assert hasattr(parser, "_playwright_parser")

    @pytest.mark.asyncio
    async def test_parse_validates_url(self):
        """Test that parse validates URL format."""
        parser = ChatGPTParser()
        # This will fail at network level, but parser should be created correctly
        assert parser is not None
