"""Export option model shared by API, MCP, and exporters."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class MarkdownFormat(str, Enum):
    """Supported markdown output formats."""

    AI_READABLE = "ai_readable"
    TRANSCRIPT = "transcript"
    COMPACT = "compact"


@dataclass(slots=True)
class ExportOptions:
    """Options that control markdown export behavior."""

    format: str = MarkdownFormat.AI_READABLE.value
    include_images: bool = True
    include_metadata: bool = True
    include_frontmatter: bool = True
    create_index: bool = True
    create_manifest: bool = True
    create_messages: bool = True
    file_basename: str = "conversation"

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "ExportOptions":
        """Create options from a plain dict, ignoring unknown keys."""
        if not data:
            return cls()
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        values = {key: value for key, value in data.items() if key in allowed}
        options = cls(**values)
        if options.format not in {fmt.value for fmt in MarkdownFormat}:
            options.format = MarkdownFormat.AI_READABLE.value
        options.file_basename = options.file_basename.strip() or "conversation"
        return options

    def to_dict(self) -> dict[str, Any]:
        """Serialize options for task persistence and API responses."""
        return asdict(self)
