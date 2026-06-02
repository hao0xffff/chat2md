"""Unit tests for ImageResource model."""
import pytest

from app.domain.model.image_resource import (
    ImageResource,
    infer_mime_type,
    generate_image_filename,
    SUPPORTED_IMAGE_TYPES,
)


class TestImageResource:
    """Tests for ImageResource model."""

    def test_creation(self):
        """Test basic image resource creation."""
        img = ImageResource(
            id="img_1",
            url="https://example.com/image.png"
        )
        assert img.id == "img_1"
        assert img.url == "https://example.com/image.png"
        assert img.downloaded is False
        assert img.local_path is None

    def test_infer_mime_type(self):
        """Test MIME type inference from URL."""
        assert infer_mime_type("https://example.com/image.png") == "image/png"
        assert infer_mime_type("https://example.com/image.jpg") == "image/jpeg"
        assert infer_mime_type("https://example.com/image.jpeg") == "image/jpeg"
        assert infer_mime_type("https://example.com/image.webp") == "image/webp"
        assert infer_mime_type("https://example.com/image.gif") == "image/gif"
        assert infer_mime_type("https://example.com/image.svg") == "application/octet-stream"

    def test_generate_image_filename(self):
        """Test filename generation."""
        assert generate_image_filename("https://example.com/image.png") == "image_1.png"
        assert generate_image_filename("https://example.com/photo.jpg") == "image_1.jpg"
        assert generate_image_filename("https://example.com/img", index=2) == "image_3.png"

    def test_mark_downloaded(self):
        """Test marking image as downloaded."""
        img = ImageResource(id="img_1", url="https://example.com/image.png")
        img.mark_downloaded("/output/images/image_1.png")

        assert img.downloaded is True
        assert img.local_path == "/output/images/image_1.png"
        assert img.is_downloaded

    def test_local_filename(self):
        """Test getting local filename from path."""
        img = ImageResource(id="img_1", url="https://example.com/image.png")
        img.mark_downloaded("/output/images/image_1.png")

        assert img.local_filename == "image_1.png"

    def test_local_filename_with_windows_path(self):
        """Test getting local filename from Windows path."""
        img = ImageResource(id="img_1", url="https://example.com/image.png")
        img.mark_downloaded("D:\\output\\images\\image_1.png")

        assert img.local_filename == "image_1.png"

    def test_supported_image_types(self):
        """Test supported image types constant."""
        assert "png" in SUPPORTED_IMAGE_TYPES
        assert "jpg" in SUPPORTED_IMAGE_TYPES
        assert "jpeg" in SUPPORTED_IMAGE_TYPES
        assert "webp" in SUPPORTED_IMAGE_TYPES
        assert "gif" in SUPPORTED_IMAGE_TYPES

    def test_filename_auto_generated(self):
        """Test that filename is auto-generated if not provided."""
        img = ImageResource(id="img_1", url="https://example.com/photo.png")
        assert img.filename == "image_1.png"

    def test_filename_from_url_with_query_params(self):
        """Test filename generation from URL with query parameters."""
        img = ImageResource(
            id="img_1",
            url="https://example.com/image.png?v=123&token=abc"
        )
        assert img.filename == "image_1.png"

    def test_metadata(self):
        """Test image metadata."""
        img = ImageResource(
            id="img_1",
            url="https://example.com/image.png",
            metadata={"width": 800, "height": 600}
        )
        assert img.metadata["width"] == 800
        assert img.metadata["height"] == 600