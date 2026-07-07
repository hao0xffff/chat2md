"""Playwright-based Gemini parser for share links."""
import time
from typing import Any

from playwright.sync_api import sync_playwright, Page

import structlog

from app.domain.model.conversation import Conversation
from app.domain.model.block import Block, BlockType
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform
from app.common.utils import generate_id
from app.config.settings import settings

logger = structlog.get_logger()


class PlaywrightGeminiParser:
    """
    Gemini parser using Playwright for share links.

    Uses browser automation to handle the modern Gemini
    SPA (Single Page Application) that loads conversation
    data dynamically via JavaScript.
    """

    def __init__(self, proxy_url: str | None = None):
        self._proxy_url = proxy_url or settings.http_proxy
        self._logger = logger.bind(component="gemini_parser")

    def parse(self, url: str) -> Conversation:
        """
        Parse a Gemini share link using Playwright.

        Args:
            url: The Gemini share link URL.

        Returns:
            A Conversation domain model.
        """
        with sync_playwright() as p:
            args = [f"--proxy-server={self._proxy_url}"] if self._proxy_url else []
            browser = p.chromium.launch(headless=True, args=args)
            try:
                context = browser.new_context()
                page = context.new_page()

                self._logger.info("navigating_to_url", url=url)
                page.goto(url, timeout=60000)
                page.wait_for_load_state("domcontentloaded")

                time.sleep(5)

                conversation_id = self._extract_conversation_id(url)
                title = self._extract_title(page)

                messages, image_data = self._extract_messages(page)

                images = []
                for img_info in image_data:
                    img_resource = ImageResource(
                        id=img_info["id"],
                        url=img_info["url"],
                        metadata={**img_info["metadata"], "alt_text": img_info["alt"]}
                    )
                    images.append(img_resource)

                conversation = Conversation(
                    id=conversation_id,
                    platform=Platform.GEMINI,
                    platform_conversation_id=conversation_id,
                    title=title or "Untitled Gemini Conversation",
                    blocks=messages,
                    images=images,
                )

                self._logger.info(
                    "parse_completed",
                    conversation_id=conversation_id,
                    message_count=len(messages),
                    image_count=len(images)
                )

                return conversation

            finally:
                browser.close()

    def _extract_conversation_id(self, url: str) -> str:
        """Extract conversation ID from URL."""
        parts = url.rstrip("/").split("/")
        return parts[-1] if parts else generate_id()

    def _extract_title(self, page: Page) -> str:
        """Extract conversation title from page."""
        try:
            og_title = page.query_selector('meta[property="og:title"]')
            if og_title:
                content = og_title.get_attribute("content")
                if content and "Gemini" not in content:
                    return content.strip()
            return page.title().replace("Gemini - ", "").strip()
        except Exception:
            return "Untitled Gemini Conversation"

    def _extract_messages(self, page: Page) -> tuple[list[Block], list[dict]]:
        """
        Extract messages and images from the page.

        Gemini structure:
        - Each turn contains both user query and model response
        - Text format: "You said\n\nUSER_MESSAGE\n\nMODEL_RESPONSE_1\n\nMODEL_RESPONSE_2..."
        """
        messages: list[Block] = []
        image_urls: list[dict] = []

        try:
            turns = page.query_selector_all('[class*="turn"]')

            for turn_idx, turn in enumerate(turns):
                html = turn.inner_html()

                # Extract images from this turn
                img_elements = turn.query_selector_all("img")
                for img_idx, img in enumerate(img_elements):
                    img_url = img.get_attribute("src")
                    if img_url and img_url.startswith("http"):
                        image_id = f"img_{turn_idx}_{img_idx}"
                        image_urls.append({
                            "id": image_id,
                            "url": img_url,
                            "alt": img.get_attribute("alt") or f"image_{image_id}",
                            "metadata": {"turn_index": turn_idx}
                        })

                # Get full text of the turn
                full_text = turn.inner_text()

                # Gemini format: "You said\n\nUSER_MESSAGE\n\nMODEL_RESPONSE_1\n\nMODEL_RESPONSE_2..."
                if "You said\n\n" not in full_text:
                    continue

                parts = full_text.split("You said\n\n", 1)
                if len(parts) < 2:
                    continue

                rest = parts[1]

                # Split by single \n\n to separate user and model content
                parts = rest.split('\n\n', 1)

                if len(parts) == 1:
                    # No blank line found, treat entire content as user message
                    segment = parts[0].strip()
                    if segment:
                        block = Block(
                            id=generate_id(),
                            block_type=BlockType.TEXT,
                            content=segment,
                            metadata={"role": "user", "turn_index": turn_idx, "segment_index": 0}
                        )
                        messages.append(block)
                else:
                    user_content, model_content = parts

                    # First part is user message
                    user_content = user_content.strip()
                    if user_content:
                        block = Block(
                            id=generate_id(),
                            block_type=BlockType.TEXT,
                            content=user_content,
                            metadata={"role": "user", "turn_index": turn_idx, "segment_index": 0}
                        )
                        messages.append(block)

                    # Second part is model content - keep as one message
                    model_content = model_content.strip()
                    if model_content:
                        block = Block(
                            id=generate_id(),
                            block_type=BlockType.TEXT,
                            content=model_content,
                            metadata={"role": "model", "turn_index": turn_idx, "segment_index": 1}
                        )
                        messages.append(block)

        except Exception as e:
            self._logger.error("message_extraction_failed", error=str(e))

        return messages, image_urls
