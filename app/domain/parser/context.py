"""Parser context - accumulates data during parsing."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.model.block import Block
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform


@dataclass
class ParserContext:
    """
    Parser Context - accumulates data during the parsing process.

    This dataclass is passed through the entire parsing pipeline,
    allowing each stage to accumulate data for the final result.
    """
    url: str
    raw_html: str | None = None
    raw_json: dict | None = None
    platform: Platform | None = None
    conversation_id: str | None = None
    title: str | None = None
    created_at: datetime | None = None
    blocks: list[Block] = field(default_factory=list)
    images: list[ImageResource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_block(self, block: Block) -> None:
        """Add a content block."""
        self.blocks.append(block)

    def add_blocks(self, blocks: list[Block]) -> None:
        """Add multiple content blocks."""
        self.blocks.extend(blocks)

    def add_image(self, image: ImageResource) -> None:
        """Add an image reference."""
        self.images.append(image)

    def add_images(self, images: list[ImageResource]) -> None:
        """Add multiple image references."""
        self.images.extend(images)

    def set_meta(self, key: str, value: Any) -> None:
        """Set metadata."""
        self.metadata[key] = value

    def get_meta(self, key: str, default: Any = None) -> Any:
        """Get metadata."""
        return self.metadata.get(key, default)