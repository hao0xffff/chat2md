"""API request/response schemas using Pydantic v2."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Request schema for single export."""
    url: str = Field(..., description="AI platform share link URL")
    output_dir: str | None = Field(None, description="Output directory (optional, defaults to settings.output_dir)")

    model_config = {
        "json_schema_extra": {
            "example": {"url": "https://chatgpt.com/share/abc123", "output_dir": "/path/to/output"}
        }
    }


class BatchExportRequest(BaseModel):
    """Request schema for batch export."""
    urls: list[str] = Field(..., min_length=1, max_length=100)
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