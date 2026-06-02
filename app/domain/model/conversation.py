"""Conversation model - the source conversation from AI platforms."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.model.block import Block
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform


@dataclass
class Conversation:
    """
    Conversation - the source conversation from an AI platform.

    This is the raw conversation data obtained from parsing
    a share link. It's different from KnowledgeDocument which
    is the processed export format.
    """
    id: str
    platform: Platform
    platform_conversation_id: str
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    blocks: list[Block] = field(default_factory=list)
    images: list[ImageResource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_block(self, block: Block) -> None:
        """Add a content block to the conversation."""
        self.blocks.append(block)

    def add_image(self, image: ImageResource) -> None:
        """Add an image reference to the conversation."""
        self.images.append(image)

    @property
    def message_count(self) -> int:
        """Get total number of content blocks."""
        return len(self.blocks)