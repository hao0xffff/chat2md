"""ChatGPT parser implementation using Playwright for modern SPA."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import structlog

from app.domain.model.conversation import Conversation
from app.domain.parser.base import BaseParser
from app.domain.parser.registry import register_parser
from app.domain.value_objects import Platform
from app.common.exceptions import ParserException

logger = structlog.get_logger()

# Thread pool for running Playwright sync code in async context
_playwright_executor = ThreadPoolExecutor(max_workers=2)


@register_parser(Platform.CHATGPT)
class ChatGPTParser(BaseParser):
    """
    ChatGPT share link parser using Playwright.

    Uses Playwright to handle the modern ChatGPT SPA that loads
    conversation data dynamically via JavaScript.
    """

    def __init__(self, proxy_url: str | None = None):
        super().__init__()
        self._proxy_url = proxy_url or "http://127.0.0.1:7890"
        self._playwright_parser = None
        self._url = ""

    def _get_playwright_parser(self):
        """Lazy-load Playwright parser."""
        if self._playwright_parser is None:
            from app.infrastructure.parser.playwright_parser import PlaywrightChatGPTParser
            self._playwright_parser = PlaywrightChatGPTParser(proxy_url=self._proxy_url)
        return self._playwright_parser

    async def parse(self, url: str) -> Conversation:
        """
        Execute parsing using Playwright.

        Overrides the template method to use Playwright directly
        since the modern ChatGPT SPA requires JavaScript rendering.
        Uses ThreadPoolExecutor to run sync Playwright code in async context.
        """
        self._url = url
        platform = self._detect_platform(url)

        self._logger.info("parse_started", url=url, platform=platform.value)

        try:
            loop = asyncio.get_event_loop()
            parser = self._get_playwright_parser()

            # Run Playwright sync parse in thread pool to avoid blocking event loop
            conversation = await loop.run_in_executor(
                _playwright_executor,
                parser.parse,
                url
            )

            self._logger.info("parse_completed", message_count=len(conversation.blocks))
            return conversation

        except Exception as e:
            self._logger.error("parse_failed", error=str(e), error_type=type(e).__name__)
            raise ParserException(
                message=f"Failed to parse URL: {url}",
                parser_type=self.__class__.__name__,
                url=url
            ) from e

    async def fetch(self, url: str) -> str:
        """Fetch - not used for Playwright parser."""
        return ""

    def extract(self, html: str) -> dict:
        """Extract - not used for Playwright parser."""
        return {}

    def transform(self, data: dict) -> Conversation:
        """Transform - uses Playwright internally."""
        raise NotImplementedError("Use parse() method instead")