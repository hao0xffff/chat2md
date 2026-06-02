"""Unit tests for common utilities."""
import pytest
from pathlib import Path
import tempfile
import shutil

from app.common.utils import (
    generate_id,
    generate_task_id,
    sanitize_filename,
    ensure_dir,
    sanitize_conversation_title,
    extract_domain_from_url,
    parse_content_type,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_generates_string(self):
        """Test that generate_id returns a string."""
        assert isinstance(generate_id(), str)

    def test_unique_ids(self):
        """Test that IDs are unique."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestGenerateTaskId:
    """Tests for generate_task_id function."""

    def test_has_prefix(self):
        """Test that task ID has correct prefix."""
        assert generate_task_id().startswith("task_")

    def test_length(self):
        """Test task ID length."""
        task_id = generate_task_id()
        assert len(task_id) == 17  # "task_" + 12 chars


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_normal_filename(self):
        """Test normal filename passes through."""
        assert sanitize_filename("normal.txt") == "normal.txt"

    def test_removes_special_chars(self):
        """Test special characters are removed."""
        assert sanitize_filename("file<>:\"/\\|?*.txt") == "filetxt"
        assert sanitize_filename("file|name.txt") == "filenametxt"

    def test_replaces_spaces(self):
        """Test spaces are replaced."""
        assert sanitize_filename("my file name.txt") == "my_file_name.txt"

    def test_trims_dots(self):
        """Test leading/trailing dots are trimmed."""
        assert sanitize_filename(".hidden.") == "hidden"
        assert sanitize_filename("...multiple...") == "multiple"

    def test_empty_defaults(self):
        """Test empty string defaults to 'unnamed'."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("<>:\"/\\|?*") == "unnamed"

    def test_max_length(self):
        """Test filename is truncated to 255 chars."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == 255


class TestEnsureDir:
    """Tests for ensure_dir function."""

    def test_creates_directory(self):
        """Test directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test" / "nested"
            ensure_dir(test_dir)
            assert test_dir.exists()
            assert test_dir.is_dir()

    def test_existing_dir(self):
        """Test existing directory is not error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_dir(Path(tmpdir))
            assert Path(tmpdir).exists()


class TestSanitizeConversationTitle:
    """Tests for sanitize_conversation_title function."""

    def test_normal_title(self):
        """Test normal title passes through."""
        assert sanitize_conversation_title("Normal Title") == "Normal_Title"

    def test_empty_title_default(self):
        """Test empty title uses default."""
        assert sanitize_conversation_title("", default="Default") == "Default"
        assert sanitize_conversation_title("   ", default="Default") == "Default"

    def test_strips_and_sanitizes(self):
        """Test title is stripped and sanitized."""
        assert sanitize_conversation_title("  Title with spaces  ") == "Title_with_spaces"
        assert sanitize_conversation_title("Title|With|Pipes") == "TitleWithPipes"

    def test_truncates_long_titles(self):
        """Test long titles are truncated."""
        long_title = "a" * 300
        result = sanitize_conversation_title(long_title)
        assert len(result) == 200


class TestExtractDomainFromUrl:
    """Tests for extract_domain_from_url function."""

    def test_extracts_domain(self):
        """Test domain is extracted."""
        assert extract_domain_from_url("https://chatgpt.com/share/abc") == "chatgpt.com"
        assert extract_domain_from_url("https://gemini.google.com/share/abc") == "gemini.google.com"

    def test_handles_http(self):
        """Test HTTP URLs."""
        assert extract_domain_from_url("http://example.com/path") == "example.com"

    def test_unknown_on_failure(self):
        """Test 'unknown' is returned on parse failure."""
        assert extract_domain_from_url("invalid-url") == "unknown"


class TestParseContentType:
    """Tests for parse_content_type function."""

    def test_parses_simple(self):
        """Test parsing simple content type."""
        mime, charset = parse_content_type("text/html")
        assert mime == "text/html"
        assert charset == "utf-8"

    def test_parses_with_charset(self):
        """Test parsing content type with charset."""
        mime, charset = parse_content_type("text/html; charset=iso-8859-1")
        assert mime == "text/html"
        assert charset == "iso-8859-1"

    def test_default_charset(self):
        """Test default charset is utf-8."""
        _, charset = parse_content_type("application/json")
        assert charset == "utf-8"

    def test_none_input(self):
        """Test None input."""
        _, charset = parse_content_type(None)
        assert charset == "utf-8"