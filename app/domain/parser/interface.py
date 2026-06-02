"""Parser interface - base interface for all parsers."""
from abc import ABC, abstractmethod

from app.domain.model.conversation import Conversation


class ConversationParser(ABC):
    """
    Conversation Parser interface.

    All platform-specific parsers must implement this interface.
    The parser is responsible for fetching a share link page,
    extracting the conversation data, and transforming it into
    a Conversation domain model.
    """

    @abstractmethod
    async def parse(self, url: str) -> Conversation:
        """
        Parse a share link URL and extract the conversation.

        Args:
            url: The share link URL from an AI platform.

        Returns:
            A Conversation domain model with all extracted data.

        Raises:
            ParserException: If parsing fails.
            PlatformNotSupportedException: If the platform is not supported.
        """
        pass

    @abstractmethod
    async def fetch(self, url: str) -> str:
        """
        Fetch the raw HTML content from the URL.

        Args:
            url: The URL to fetch.

        Returns:
            Raw HTML content as string.
        """
        pass

    @abstractmethod
    def extract(self, html: str) -> dict:
        """
        Extract structured data from HTML.

        The implementation depends on the platform's page structure.
        Some platforms embed JSON data, others require HTML parsing.

        Args:
            html: Raw HTML content.

        Returns:
            A dictionary with extracted data.
        """
        pass

    @abstractmethod
    def transform(self, data: dict) -> Conversation:
        """
        Transform extracted data into a Conversation model.

        Args:
            data: Extracted data dictionary.

        Returns:
            A Conversation domain model.
        """
        pass