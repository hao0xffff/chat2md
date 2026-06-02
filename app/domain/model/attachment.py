"""Attachment model."""
from dataclasses import dataclass
from typing import Any


@dataclass
class Attachment:
    """
    Attachment - represents a file attachment in a message.

    Unlike ImageResource, attachments are typically documents
    or files that were shared in the conversation.
    """
    id: str
    message_id: str
    name: str
    file_type: str
    url: str
    size: int | None = None
    local_path: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_downloaded(self) -> bool:
        return self.local_path is not None

    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.file_type.lower()