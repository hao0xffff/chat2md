"""Block model - represents content blocks in a conversation."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BlockType(Enum):
    """Types of content blocks."""
    TEXT = "text"
    CODE = "code"
    TABLE = "table"
    IMAGE = "image"
    QUOTE = "quote"
    LIST = "list"


@dataclass
class Block:
    """
    Content block - represents a single piece of content in a message.

    Replaces the previous Message model to provide more flexibility
    in representing different types of content.
    """
    id: str
    block_type: BlockType
    content: str | None = None
    language: str | None = None  # for CODE block
    headers: list[str] | None = None  # for TABLE block
    rows: list[list[str]] | None = None  # for TABLE block
    image_url: str | None = None  # for IMAGE block
    alt_text: str | None = None  # for IMAGE block
    level: int | None = None  # for QUOTE block (quote level)
    items: list[str] | None = None  # for LIST block
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_text(self) -> bool:
        return self.block_type == BlockType.TEXT

    @property
    def is_code(self) -> bool:
        return self.block_type == BlockType.CODE

    @property
    def is_table(self) -> bool:
        return self.block_type == BlockType.TABLE

    @property
    def is_image(self) -> bool:
        return self.block_type == BlockType.IMAGE

    @property
    def is_quote(self) -> bool:
        return self.block_type == BlockType.QUOTE

    @property
    def is_list(self) -> bool:
        return self.block_type == BlockType.LIST

    def to_markdown(self) -> str:
        """Convert block to markdown format."""
        if self.is_text:
            return self.content or ""
        elif self.is_code:
            lang = self.language or ""
            code = self.content or ""
            return f"```{lang}\n{code}\n```"
        elif self.is_table:
            return self._format_table()
        elif self.is_image:
            alt = self.alt_text or "image"
            url = self.image_url or ""
            return f"![{alt}]({url})"
        elif self.is_quote:
            content = self.content or ""
            level = self.level or 1
            prefix = ">" * level
            return f"{prefix} {content}"
        elif self.is_list:
            return self._format_list()
        return ""

    def _format_table(self) -> str:
        """Format table block as markdown."""
        if not self.headers or not self.rows:
            return ""

        lines = []
        lines.append("| " + " | ".join(self.headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(self.headers)) + " |")
        for row in self.rows:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def _format_list(self) -> str:
        """Format list block as markdown."""
        if not self.items:
            return ""
        return "\n".join([f"- {item}" for item in self.items])