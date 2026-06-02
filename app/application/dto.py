"""Application DTOs using Pydantic."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Request DTO for single export."""
    url: str = Field(..., description="AI platform share link URL")

    model_config = {
        "json_schema_extra": {
            "example": {"url": "https://chatgpt.com/share/abc123"}
        }
    }


class BatchExportRequest(BaseModel):
    """Request DTO for batch export."""
    urls: list[str] = Field(..., min_length=1, max_length=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "urls": [
                    "https://chatgpt.com/share/abc123",
                    "https://chatgpt.com/share/def456"
                ]
            }
        }
    }


class ExportResponse(BaseModel):
    """Response DTO for export operation."""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response DTO for task status."""
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
    """Response DTO for download operation."""
    task_id: str
    output_dir: str
    file_count: int
    image_count: int
    download_url: str


class ErrorResponse(BaseModel):
    """Response DTO for errors."""
    error: str
    code: str
    detail: str | None = None