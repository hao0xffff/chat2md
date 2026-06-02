"""Image resource model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any


SUPPORTED_IMAGE_TYPES = {"png", "jpg", "jpeg", "webp", "gif"}


def infer_mime_type(url: str) -> str:
    """Infer MIME type from URL."""
    ext = url.lower().split(".")[-1].split("?")[0]
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    return mime_map.get(ext, "application/octet-stream")


def generate_image_filename(url: str, index: int = 0) -> str:
    """Generate a filename from URL."""
    ext = url.lower().split(".")[-1].split("?")[0]
    if ext not in SUPPORTED_IMAGE_TYPES:
        ext = "png"
    return f"image_{index + 1}.{ext}"


@dataclass
class ImageResource:
    """
    Image resource - represents an image that can be downloaded.

    Images are referenced in messages and need to be downloaded
    and saved locally during the export process.
    """
    id: str
    url: str
    filename: str | None = None
    mime_type: str | None = None
    local_path: str | None = None
    downloaded: bool = False
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.filename is None:
            self.filename = generate_image_filename(self.url)
        if self.mime_type is None:
            self.mime_type = infer_mime_type(self.url)

    def mark_downloaded(self, local_path: str) -> None:
        """Mark the image as downloaded with the local path."""
        self.local_path = local_path
        self.downloaded = True

    @property
    def is_downloaded(self) -> bool:
        return self.downloaded and self.local_path is not None

    @property
    def local_filename(self) -> str | None:
        """Get just the filename from local path."""
        if self.local_path:
            return self.local_path.split("/")[-1].split("\\")[-1]
        return None