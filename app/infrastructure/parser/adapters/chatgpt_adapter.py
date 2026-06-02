"""Adapter for ChatGPT share link data."""
import json
import re
from typing import Any

from app.domain.model.block import Block, BlockType
from app.domain.model.conversation import Conversation
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform
from app.common.utils import generate_id


class ChatGPTAdapter:
    """
    Adapter for ChatGPT share link data.

    ChatGPT embeds conversation data in the page as JSON in a script tag.
    This adapter extracts and transforms that data into domain models.
    """

    def __init__(self):
        self._conversation_id = None
        self._title = None
        self._created_at = None
        self._blocks: list[Block] = []
        self._images: list[ImageResource] = []

    def adapt(self, html: str) -> Conversation:
        """
        Adapt HTML to Conversation model.

        Args:
            html: Raw HTML from ChatGPT share page.

        Returns:
            A Conversation domain model.
        """
        data = self._extract_json(html)
        if not data:
            raise ValueError("Failed to extract conversation data from ChatGPT page")

        self._conversation_id = data.get("id", generate_id())
        self._title = data.get("title", "Untitled")
        self._created_at = data.get("create_time")

        mapping = data.get("mapping", {})
        self._process_messages(mapping)

        return Conversation(
            id=self._conversation_id,
            platform=Platform.CHATGPT,
            platform_conversation_id=self._conversation_id,
            title=self._title,
            created_at=self._created_at,
            blocks=self._blocks,
            images=self._images,
        )

    def _extract_json(self, html: str) -> dict | None:
        """Extract JSON data from script tag in HTML."""
        # ChatGPT stores conversation data in a window.__NEXT_DATA__ script
        patterns = [
            r'window\.__NEXT_DATA__\s*=\s*({.*?})\s*</script>',
            r'"conversation":\s*({.*?}),"conversationMessages',
            r'id="__NEXT_DATA__"[^>]*>([^<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if match.lastindex == 1 else match.group(0)
                    json_str = json_str.replace("window.__NEXT_DATA__ = ", "")
                    data = json.loads(json_str)
                    return self._extract_conversation_data(data)
                except (json.JSONDecodeError, AttributeError):
                    continue

        # Try to find conversation data more directly
        if '"id":"' in html and '"title":"' in html:
            try:
                # Try to find the conversation object
                start = html.find('"conversation":{')
                if start == -1:
                    start = html.find('"messages":{')
                if start != -1:
                    # Find the JSON object
                    depth = 0
                    i = start
                    while i < len(html):
                        if html[i] == '{':
                            depth += 1
                        elif html[i] == '}':
                            depth -= 1
                            if depth == 0:
                                json_str = html[start:i+1]
                                data = json.loads(json_str)
                                return self._extract_conversation_data(data)
                        i += 1
            except Exception:
                pass

        return None

    def _extract_conversation_data(self, data: dict) -> dict | None:
        """Extract conversation data from NEXT_DATA structure."""
        try:
            # Navigate through NEXT_DATA structure
            props = data.get("props", {})
            page_props = props.get("pageProps", {})
            server_response = page_props.get("serverResponse", {})
            conversation_data = server_response.get("data", {})
            if conversation_data.get("id"):
                return conversation_data

            # Try alternative paths
            if data.get("id"):
                return data

            # Try to find in the structure
            for key in ["conversation", "data", "result"]:
                if key in data and isinstance(data[key], dict) and data[key].get("id"):
                    return data[key]

            return None
        except Exception:
            return None

    def _process_messages(self, mapping: dict) -> None:
        """Process messages from the mapping structure."""
        if not mapping:
            return

        # Sort messages by their position
        sorted_nodes = sorted(
            mapping.items(),
            key=lambda x: (x[1].get("clientId", ""), x[0])
        )

        for node_id, node_data in sorted_nodes:
            message = node_data.get("message")
            if not message:
                continue

            if message.get("author", {}).get("role") == "system":
                continue

            block = self._create_block_from_message(message)
            if block:
                self._blocks.append(block)

    def _create_block_from_message(self, message: dict) -> Block | None:
        """Create a Block from a ChatGPT message."""
        role = message.get("author", {}).get("role", "user")
        content = message.get("content", {})

        # Extract text content
        text_parts = []
        if content.get("content_type") == "text":
            parts = content.get("parts", [])
            text_parts.extend(parts)
        elif content.get("content_type") == "code":
            language = content.get("language", "")
            code = "".join(content.get("code", []))
            if code:
                return Block(
                    id=generate_id(),
                    block_type=BlockType.CODE,
                    content=code,
                    language=language,
                    metadata={"role": role, "message_id": message.get("id")}
                )

        if text_parts:
            text = "\n".join(str(p) for p in text_parts)
            return Block(
                id=generate_id(),
                block_type=BlockType.TEXT,
                content=text,
                metadata={"role": role, "message_id": message.get("id")}
            )

        # Handle other content types
        content_type = content.get("content_type", "")
        if content_type == "image_asset":
            asset_id = content.get("asset_id", "")
            if asset_id:
                image_url = f"https://assetcdn.999.so/{asset_id}"
                return Block(
                    id=generate_id(),
                    block_type=BlockType.IMAGE,
                    image_url=image_url,
                    alt_text=content.get("name", "image"),
                    metadata={"role": role, "message_id": message.get("id")}
                )

        return None