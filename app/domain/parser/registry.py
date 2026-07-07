"""Parser registry - manages all registered parsers."""
from typing import Type

from app.domain.parser.interface import ConversationParser
from app.domain.value_objects import Platform
from app.common.exceptions import PlatformNotSupportedException


class ParserRegistry:
    """
    Parser Registry - manages platform-specific parsers.

    This is a registry pattern implementation that allows runtime
    registration of parsers. Each parser registers itself with
    a specific platform and can be retrieved by platform.
    """
    _parsers: dict[str, Type[ConversationParser]] = {}

    @classmethod
    def register(cls, platform: Platform, parser_class: Type[ConversationParser]) -> None:
        """
        Register a parser for a specific platform.

        Args:
            platform: The platform enum value.
            parser_class: The parser class to register.
        """
        cls._parsers[platform.value] = parser_class

    @classmethod
    def get(cls, platform: Platform) -> Type[ConversationParser]:
        """
        Get the parser class for a platform.

        Args:
            platform: The platform enum value.

        Returns:
            The parser class for the platform.

        Raises:
            PlatformNotSupportedException: If no parser is registered for the platform.
        """
        from app.config.settings import settings

        enabled = set(settings.enabled_platforms)
        if platform.value not in enabled:
            supported = [p for p in cls._parsers.keys() if p in enabled]
            raise PlatformNotSupportedException(platform.value, supported)

        if platform.value not in cls._parsers:
            supported = [p for p in cls._parsers.keys() if p in enabled]
            raise PlatformNotSupportedException(platform.value, supported)
        return cls._parsers[platform.value]

    @classmethod
    def detect_platform(cls, url: str) -> Platform:
        """
        Detect the platform from a URL.

        Args:
            url: The share link URL.

        Returns:
            The detected Platform enum value.

        Raises:
            PlatformNotSupportedException: If the platform cannot be detected.
        """
        from app.config.settings import settings

        url_lower = url.lower()
        for platform_value, patterns in settings.platform_url_patterns.items():
            if any(pattern.lower() in url_lower for pattern in patterns):
                try:
                    return Platform(platform_value)
                except ValueError:
                    continue
        supported = list(settings.platform_url_patterns.keys())
        raise PlatformNotSupportedException(url, supported)

    @classmethod
    def create_parser(cls, url: str) -> ConversationParser:
        """
        Create a parser instance for a URL.

        This method detects the platform from the URL and
        creates an instance of the registered parser.

        Args:
            url: The share link URL.

        Returns:
            An instance of the appropriate parser.

        Raises:
            PlatformNotSupportedException: If the platform is not supported.
        """
        platform = cls.detect_platform(url)
        parser_class = cls.get(platform)
        return parser_class()

    @classmethod
    def is_registered(cls, platform: Platform) -> bool:
        """Check if a platform has a registered parser."""
        return platform.value in cls._parsers

    @classmethod
    def registered_platforms(cls) -> list[str]:
        """Get list of registered platform values."""
        from app.config.settings import settings

        enabled = set(settings.enabled_platforms)
        return [platform for platform in cls._parsers.keys() if platform in enabled]

    @classmethod
    def available_platforms(cls) -> list[dict[str, object]]:
        """Return configured platform metadata for API/UI clients."""
        from app.config.settings import settings

        enabled = set(settings.enabled_platforms)
        items = []
        for platform in Platform:
            patterns = settings.platform_url_patterns.get(platform.value, [])
            registered = platform.value in cls._parsers
            items.append({
                "id": platform.value,
                "name": platform.value.title(),
                "enabled": platform.value in enabled,
                "registered": registered,
                "patterns": patterns,
            })
        return items


def register_parser(platform: Platform):
    """
    Decorator to register a parser for a platform.

    Usage:
        @register_parser(Platform.CHATGPT)
        class ChatGPTParser(BaseParser):
            ...
    """
    def decorator(cls: Type[ConversationParser]) -> Type[ConversationParser]:
        ParserRegistry.register(platform, cls)
        return cls
    return decorator
