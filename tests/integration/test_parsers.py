"""Integration tests for parsers."""
import pytest

from app.domain.parser.registry import ParserRegistry
from app.domain.value_objects import Platform


class TestParserRegistry:
    """Integration tests for parser registry."""

    def test_chatgpt_parser_is_registered(self):
        """Test ChatGPT parser is registered."""
        assert ParserRegistry.is_registered(Platform.CHATGPT)

    def test_gemini_parser_is_registered(self):
        """Test Gemini parser is registered."""
        assert ParserRegistry.is_registered(Platform.GEMINI)

    def test_doubao_parser_is_registered(self):
        """Test Doubao parser is registered."""
        assert ParserRegistry.is_registered(Platform.DOUBAN)

    def test_detect_chatgpt_url(self):
        """Test ChatGPT URL detection."""
        platform = ParserRegistry.detect_platform("https://chatgpt.com/share/abc123")
        assert platform == Platform.CHATGPT

    def test_detect_gemini_url(self):
        """Test Gemini URL detection."""
        platform = ParserRegistry.detect_platform("https://gemini.google.com/share/abc123")
        assert platform == Platform.GEMINI

    def test_detect_doubao_url(self):
        """Test Doubao URL detection."""
        platform = ParserRegistry.detect_platform("https://doubao.com/share/abc123")
        assert platform == Platform.DOUBAN

    def test_create_parser_returns_correct_type(self):
        """Test create_parser returns correct parser type."""
        parser = ParserRegistry.create_parser("https://chatgpt.com/share/abc123")
        from app.infrastructure.parser.chatgpt import ChatGPTParser
        assert isinstance(parser, ChatGPTParser)

    def test_parser_classes_have_required_methods(self):
        """Test all parser classes have required interface methods."""
        from app.domain.parser.interface import ConversationParser
        from app.infrastructure.parser.chatgpt import ChatGPTParser
        from app.infrastructure.parser.gemini import GeminiParser
        from app.infrastructure.parser.doubao import DoubaoParser

        for parser_class in [ChatGPTParser, GeminiParser, DoubaoParser]:
            assert issubclass(parser_class, ConversationParser)
            assert hasattr(parser_class, 'parse')
            assert hasattr(parser_class, 'fetch')
            assert hasattr(parser_class, 'extract')
            assert hasattr(parser_class, 'transform')