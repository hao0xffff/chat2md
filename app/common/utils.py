"""Utility functions."""
import re
import uuid
from pathlib import Path


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def generate_task_id() -> str:
    """Generate a task ID with prefix."""
    return f"task_{uuid.uuid4().hex[:12]}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: The filename to sanitize.

    Returns:
        A sanitized filename safe for use on most filesystems.
    """
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip("._")
    if not filename:
        filename = "unnamed"
    return filename[:255]


def ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path to ensure exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def sanitize_conversation_title(title: str | None, default: str = "Untitled") -> str:
    """
    Sanitize a conversation title for use as a directory name.

    Args:
        title: The original title.
        default: Default title if the original is empty.

    Returns:
        A sanitized title safe for use as a directory name.
    """
    if not title or not title.strip():
        return default
    title = title.strip()
    title = re.sub(r'[<>:"/\\|?*]', "", title)
    title = re.sub(r"\s+", "_", title)
    return title[:200] or default


def extract_domain_from_url(url: str) -> str:
    """
    Extract the domain from a URL.

    Args:
        url: The URL to extract from.

    Returns:
        The domain name.
    """
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1) if match else "unknown"


def parse_content_type(content_type: str | None) -> tuple[str, str]:
    """
    Parse a content-type header into MIME type and charset.

    Args:
        content_type: The content-type header value.

    Returns:
        A tuple of (MIME type, charset).
    """
    if not content_type:
        return "application/octet-stream", "utf-8"
    parts = content_type.split(";")
    mime = parts[0].strip()
    charset = "utf-8"
    for part in parts[1:]:
        if "charset" in part:
            charset = part.split("=")[1].strip()
    return mime, charset