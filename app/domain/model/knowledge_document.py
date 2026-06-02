"""KnowledgeDocument model - the exported document representation."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.model.block import Block
from app.domain.model.image_resource import ImageResource
from app.domain.value_objects import Platform


@dataclass
class KnowledgeDocument:
    """
    Knowledge Document - represents the final exported document.

    This is the domain model that gets exported to Markdown.
    It contains all the blocks (messages, code, images, etc.)
    and references to images that need to be downloaded.
    """
    id: str
    title: str
    platform: Platform
    conversation_id: str
    blocks: list[Block] = field(default_factory=list)
    images: list[ImageResource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def add_block(self, block: Block) -> None:
        """Add a content block to the document."""
        self.blocks.append(block)

    def add_image(self, image: ImageResource) -> None:
        """Add an image reference to the document."""
        self.images.append(image)

    @property
    def text_blocks(self) -> list[Block]:
        """Get all text blocks."""
        return [b for b in self.blocks if b.is_text]

    @property
    def code_blocks(self) -> list[Block]:
        """Get all code blocks."""
        return [b for b in self.blocks if b.is_code]

    @property
    def image_blocks(self) -> list[Block]:
        """Get all image blocks."""
        return [b for b in self.blocks if b.is_image]

    @property
    def table_blocks(self) -> list[Block]:
        """Get all table blocks."""
        return [b for b in self.blocks if b.is_table]

    @property
    def quote_blocks(self) -> list[Block]:
        """Get all quote blocks."""
        return [b for b in self.blocks if b.is_quote]

    @property
    def list_blocks(self) -> list[Block]:
        """Get all list blocks."""
        return [b for b in self.blocks if b.is_list]

    @property
    def all_markdown(self) -> str:
        """Convert entire document to markdown."""
        return "\n\n".join([block.to_markdown() for block in self.blocks])