"""API request/response schemas using Pydantic v2."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, StrictStr

from app.config.settings import settings


class ExportOptionsSchema(BaseModel):
    """Export options accepted by API and UI."""

    format: str = Field(settings.default_export_format, description="Markdown format: ai_readable, transcript, compact")
    include_images: bool = Field(settings.default_include_images, description="Download and reference images")
    include_metadata: bool = Field(settings.default_include_metadata, description="Include source and export metadata")
    include_frontmatter: bool = Field(settings.default_include_frontmatter, description="Include YAML frontmatter")
    create_index: bool = Field(settings.default_create_index, description="Create index.md")
    create_manifest: bool = Field(settings.default_create_manifest, description="Create manifest.md")
    create_messages: bool = Field(settings.default_create_messages, description="Create messages.md")
    file_basename: str = Field("conversation", description="Base filename for the main markdown file")


class ExportRequest(ExportOptionsSchema):
    """Request schema for single export."""
    url: StrictStr = Field(..., description="AI platform share link URL")
    output_dir: str | None = Field(None, description="Output directory (optional, defaults to settings.output_dir)")

    model_config = {
        "json_schema_extra": {
            "example": {"url": "https://chatgpt.com/share/abc123", "output_dir": "/path/to/output"}
        }
    }


class BatchExportRequest(ExportOptionsSchema):
    """Request schema for batch export."""
    urls: list[StrictStr] = Field(..., min_length=1, max_length=100)
    output_dir: str | None = Field(None, description="Output directory (optional, defaults to settings.output_dir)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "urls": [
                    "https://chatgpt.com/share/abc123",
                    "https://chatgpt.com/share/def456"
                ],
                "output_dir": "/path/to/output"
            }
        }
    }


class ExportResponse(BaseModel):
    """Response schema for export operation."""
    task_id: str
    status: str
    message: str
    output_dir: str | None = None


class TaskStatusResponse(BaseModel):
    """Response schema for task status."""
    task_id: str
    status: str
    progress: float
    url: str | None = None
    output_path: str | None = None
    error: str | None = None
    message_count: int = 0
    image_count: int = 0
    export_options: dict = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None = None


class DownloadResponse(BaseModel):
    """Response schema for download operation."""
    task_id: str
    output_dir: str
    file_count: int
    image_count: int
    download_url: str


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    error: str
    code: str
    detail: str | None = None


class PlatformInfo(BaseModel):
    """Configured parser platform metadata."""

    id: str
    name: str
    enabled: bool
    registered: bool
    patterns: list[str]


class ExportConfigResponse(BaseModel):
    """Runtime export configuration for API/UI clients."""

    app_name: str
    display_name: str
    english_name: str
    output_dir: str
    default_options: ExportOptionsSchema
    platforms: list[PlatformInfo]
