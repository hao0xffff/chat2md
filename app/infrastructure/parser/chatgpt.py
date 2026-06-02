"""ChatGPT parser implementation."""
from typing import Any

import structlog

from app.domain.model.conversation import Conversation
from app.domain.parser.base import BaseParser
from app.domain.parser.registry import register_parser
from app.domain.value_objects import Platform
from app.infrastructure.parser.adapters.chatgpt_adapter import ChatGPTAdapter
from app.infrastructure.client.http_client import HttpClient

logger = structlog.get_logger()


@register_parser(Platform.CHATGPT)
class ChatGPTParser(BaseParser):
    """
    ChatGPT share link parser.

    Fetches ChatGPT share page and extracts conversation data
    using the ChatGPTAdapter.
    """

    def __init__(self, http_client: HttpClient | None = None):
        super().__init__()
        self._http_client = http_client
        self._adapter = ChatGPTAdapter()

    async def fetch(self, url: str) -> str:
        """
        Fetch the ChatGPT share page HTML.

        Args:
            url: The ChatGPT share link URL.

        Returns:
            Raw HTML content.
        """
        self._logger.info("fetching_page", url=url)
        client = self._http_client or HttpClient()
        try:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
            html = await response.text()
            return html
        finally:
            if self._http_client is None:
                await client.close()

    def extract(self, html: str) -> dict:
        """
        Extract conversation data from HTML.

        Uses ChatGPTAdapter to parse the embedded JSON data.

        Args:
            html: Raw HTML from ChatGPT page.

        Returns:
            A dictionary with extracted data.
        """
        try:
            conversation = self._adapter.adapt(html)
            return {
                "conversation": conversation,
                "raw_data": {"title": conversation.title, "id": conversation.id}
            }
        except Exception as e:
            self._logger.error("extraction_failed", error=str(e))
            raise

    def transform(self, data: dict) -> Conversation:
        """
        Transform extracted data into Conversation model.

        Args:
            data: Extracted data dictionary.

        Returns:
            A Conversation domain model.
        """
        conversation = data.get("conversation")
        if not conversation:
            raise ValueError("No conversation data found")
        return conversation