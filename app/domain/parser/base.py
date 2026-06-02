"""Base parser - template method pattern implementation."""
from abc import abstractmethod
from typing import Any

import structlog

from app.domain.model.conversation import Conversation
from app.domain.parser.context import ParserContext
from app.domain.parser.interface import ConversationParser
from app.domain.value_objects import Platform
from app.common.exceptions import ParserException

logger = structlog.get_logger()


class BaseParser(ConversationParser):
    """
    Base Parser - implements the template method pattern.

    This class provides the common parsing workflow and defines
    abstract methods that subclasses must implement for
    platform-specific behavior.

    The parsing workflow:
    1. fetch() - fetch raw HTML from URL
    2. extract() - extract structured data from HTML
    3. transform() - transform data into Conversation model
    """

    def __init__(self):
        self._logger = logger.bind(component="parser", parser=self.__class__.__name__)

    async def parse(self, url: str) -> Conversation:
        """
        Execute the full parsing workflow.

        This is the template method that coordinates the parsing process.

        Args:
            url: The share link URL.

        Returns:
            A Conversation domain model.

        Raises:
            ParserException: If any step in the workflow fails.
        """
        ctx = ParserContext(url=url)
        platform = self._detect_platform(url)
        ctx.platform = platform

        self._logger.info("parse_started", url=url, platform=platform.value)

        try:
            html = await self.fetch(url)
            ctx.raw_html = html

            data = self.extract(html)
            ctx.raw_json = data

            conversation = self.transform(data)
            self._logger.info("parse_completed", message_count=len(conversation.blocks))
            return conversation

        except Exception as e:
            self._logger.error("parse_failed", error=str(e), error_type=type(e).__name__)
            raise ParserException(
                message=f"Failed to parse URL: {url}",
                parser_type=self.__class__.__name__,
                url=url
            ) from e

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

    def _detect_platform(self, url: str) -> Platform:
        """Detect platform from URL. Subclasses can override for custom detection."""
        url_lower = url.lower()
        if "chatgpt.com" in url_lower:
            return Platform.CHATGPT
        elif "gemini.google" in url_lower:
            return Platform.GEMINI
        elif "doubao.com" in url_lower:
            return Platform.DOUBAN
        raise ValueError(f"Unsupported platform for URL: {url}")

    def _generate_id(self) -> str:
        """Generate a unique ID."""
        import uuid
        return str(uuid.uuid4())

    def _sanitize_title(self, title: str) -> str:
        """Sanitize title for use as filename."""
        import re
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()