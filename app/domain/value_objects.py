"""Value objects for the domain layer."""
from enum import Enum


class Platform(Enum):
    """AI platform enumeration."""
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    DOUBAN = "doubao"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"
    QIANWEN = "qianwen"
    GROK = "grok"

    @classmethod
    def from_url(cls, url: str) -> "Platform":
        """Detect platform from URL."""
        url_lower = url.lower()
        if "chatgpt.com" in url_lower:
            return cls.CHATGPT
        elif "gemini.google" in url_lower:
            return cls.GEMINI
        elif "doubao.com" in url_lower:
            return cls.DOUBAN
        raise ValueError(f"Unsupported platform for URL: {url}")


class MessageRole(Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"