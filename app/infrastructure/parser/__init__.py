"""Infrastructure parser module."""
from app.infrastructure.parser.chatgpt import ChatGPTParser
from app.infrastructure.parser.gemini import GeminiParser
from app.infrastructure.parser.doubao import DoubaoParser

__all__ = ["ChatGPTParser", "GeminiParser", "DoubaoParser"]