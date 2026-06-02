"""Doubao parser implementation - skeleton."""
from app.domain.model.conversation import Conversation
from app.domain.parser.base import BaseParser
from app.domain.parser.registry import register_parser
from app.domain.value_objects import Platform
from app.common.exceptions import PlatformNotSupportedException


@register_parser(Platform.DOUBAN)
class DoubaoParser(BaseParser):
    """
    Doubao share link parser - skeleton implementation.

    TODO: Implement actual parsing logic for Doubao share links.
    """

    async def fetch(self, url: str) -> str:
        """Fetch the Doubao share page HTML."""
        raise NotImplementedError("Doubao parser not yet implemented")

    def extract(self, html: str) -> dict:
        """Extract conversation data from HTML."""
        raise NotImplementedError("Doubao parser not yet implemented")

    def transform(self, data: dict) -> Conversation:
        """Transform extracted data into Conversation model."""
        raise NotImplementedError("Doubao parser not yet implemented")