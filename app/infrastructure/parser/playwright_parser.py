"""Playwright-based ChatGPT parser for share links."""
import time

from playwright.sync_api import sync_playwright, Page

import structlog

from app.domain.model.conversation import Conversation
from app.domain.model.block import Block, BlockType
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform
from app.common.utils import generate_id
from app.config.settings import settings

logger = structlog.get_logger()


class PlaywrightChatGPTParser:
    """
    ChatGPT parser using Playwright for share links.

    Uses browser automation to handle the modern ChatGPT
    SPA (Single Page Application) that loads conversation
    data dynamically via JavaScript.
    """

    def __init__(self, proxy_url: str | None = None):
        self._proxy_url = proxy_url or settings.http_proxy
        self._logger = logger.bind(component="playwright_parser")

    def parse(self, url: str) -> Conversation:
        """
        Parse a ChatGPT share link using Playwright.

        Args:
            url: The ChatGPT share link URL.

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
                self._ensure_supported_page(page)
                page.wait_for_selector(
                    "[data-message-author-role]",
                    timeout=settings.parser_timeout * 1000,
                )

                # Wait for dynamic content to load
                time.sleep(1)
                self._ensure_supported_page(page)

                # Extract conversation metadata
                conversation_id = self._extract_conversation_id(url)
                title = self._extract_title(page)

                # Extract messages and images
                messages, image_data = self._extract_messages(page)
                if not messages:
                    raise ValueError("No ChatGPT messages found in share page")

                # Build image resources
                images = []
                for img_info in image_data:
                    img_resource = ImageResource(
                        id=img_info["id"],
                        url=img_info["url"],
                        metadata={**img_info["metadata"], "alt_text": img_info["alt"]}
                    )
                    images.append(img_resource)

                # Build conversation
                conversation = Conversation(
                    id=conversation_id,
                    platform=Platform.CHATGPT,
                    platform_conversation_id=conversation_id,
                    title=title,
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
        # URL format: https://chatgpt.com/share/{conversation_id}
        parts = url.rstrip("/").split("/")
        return parts[-1] if parts else generate_id()

    def _extract_title(self, page: Page) -> str:
        """Extract conversation title from page."""
        try:
            # Try to get title from og:title meta tag
            og_title = page.query_selector('meta[property="og:title"]')
            if og_title:
                content = og_title.get_attribute("content")
                if content:
                    return content.replace("ChatGPT - ", "").strip()

            # Fallback to page title
            return page.title().replace("ChatGPT - ", "").strip()
        except Exception:
            return "Untitled Conversation"

    def _ensure_supported_page(self, page: Page) -> None:
        """Fail early on bot checks and non-conversation pages."""
        title = (page.title() or "").strip().lower()
        challenge_markers = [
            "just a moment",
            "checking your browser",
            "verify you are human",
            "attention required",
        ]
        if any(marker in title for marker in challenge_markers):
            raise ValueError(f"ChatGPT share page is not accessible: {page.title()}")

    def _extract_messages(self, page: Page) -> tuple[list[Block], list[dict]]:
        """
        Extract messages and images from the page.

        Returns:
            A tuple of (messages, image_urls).
        """
        messages: list[Block] = []
        image_urls: list[dict] = []

        try:
            # Find all message elements
            message_elements = page.query_selector_all(
                "[data-message-author-role]"
            )

            for i, element in enumerate(message_elements):
                role = element.get_attribute("data-message-author-role")
                if role not in ["user", "assistant"]:
                    continue

                # Extract text content
                text = element.inner_text().strip()

                # Extract images from this message element
                img_elements = element.query_selector_all("img")
                for j, img in enumerate(img_elements):
                    img_url = img.get_attribute("src")
                    if self._is_content_image_url(img_url):
                        image_id = f"img_{i}_{j}"
                        image_urls.append({
                            "id": image_id,
                            "url": img_url,
                            "alt": img.get_attribute("alt") or f"image_{image_id}",
                            "metadata": {"role": role, "message_index": i}
                        })
                        # Add ImageBlock to messages if text is empty
                        if not text:
                            block = Block(
                                id=generate_id(),
                                block_type=BlockType.IMAGE,
                                image_url=img_url,
                                alt_text=img.get_attribute("alt") or f"image_{image_id}",
                                metadata={"role": role, "image_id": image_id, "index": i}
                            )
                            messages.append(block)

                if not text:
                    continue

                block = Block(
                    id=generate_id(),
                    block_type=BlockType.TEXT,
                    content=text,
                    metadata={"role": role, "index": i}
                )
                messages.append(block)

        except Exception as e:
            self._logger.error("message_extraction_failed", error=str(e))

        return messages, image_urls

    def _is_content_image_url(self, img_url: str | None) -> bool:
        """Return true for likely user-visible message images."""
        if not img_url or not img_url.startswith("http"):
            return False
        url = img_url.lower()
        excluded = ("avatar", "favicon", "logo", "icon", "sprite", "data:image")
        if any(part in url for part in excluded):
            return False
        included = (
            "oaiusercontent",
            "oaidalleapiprodscus",
            "/image",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".gif",
        )
        return any(part in url for part in included)


class ChatGPTParserPlaywrightAdapter:
    """
    Adapter that wraps PlaywrightChatGPTParser to work with the async BaseParser.

    Since the original architecture uses async/await but Playwright's main API
    is sync, we provide this adapter for the sync use case.
    """

    def __init__(self, proxy_url: str | None = None):
        self._parser = PlaywrightChatGPTParser(proxy_url=proxy_url)

    def parse(self, url: str) -> Conversation:
        """Synchronous parse method."""
        return self._parser.parse(url)
