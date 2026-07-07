"""API routes for the export service."""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from app.api.schemas import (
    ExportRequest,
    BatchExportRequest,
    ExportResponse,
    TaskStatusResponse,
    DownloadResponse,
    ErrorResponse,
    ExportConfigResponse,
    ExportOptionsSchema,
    PlatformInfo,
)
from app.api.dependencies import Container, container
from app.application.export_service import ExportService
from app.application.task_service import TaskService
from app.config.settings import settings
from app.domain.parser.registry import ParserRegistry
from app.common.exceptions import (
    BusinessException,
    ParserException,
    TaskNotFoundException,
    TaskNotCompletedException,
)

router = APIRouter(prefix="/api/v1", tags=["export"])


def get_export_service() -> ExportService:
    """Get export service from container."""
    return container.export_service()


def get_task_service() -> TaskService:
    """Get task service from container."""
    return container.task_service()


@router.post("/export", response_model=ExportResponse)
async def export_conversation(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends(get_export_service),
) -> ExportResponse:
    """
    Export a conversation from a share link.

    Creates an export task and returns immediately.
    The actual export runs in the background.

    Use GET /task/{task_id} to check status.
    """
    try:
        options = request.model_dump(exclude={"url", "output_dir"})
        task = await export_service.create_export_task(request.url, request.output_dir, options)
        background_tasks.add_task(export_service.execute_export, task.id)
        return ExportResponse(
            task_id=task.id,
            status=task.status.value,
            message="Export task created",
            output_dir=task.output_dir,
        )
    except ParserException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/batch", response_model=list[ExportResponse])
async def batch_export(
    request: BatchExportRequest,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends(get_export_service),
) -> list[ExportResponse]:
    """
    Batch export multiple conversations.

    Creates export tasks for all URLs and returns immediately.
    The actual exports run in the background.
    """
    responses = []
    options = request.model_dump(exclude={"urls", "output_dir"})
    for url in request.urls:
        try:
            task = await export_service.create_export_task(url, request.output_dir, options)
            background_tasks.add_task(export_service.execute_export, task.id)
            responses.append(ExportResponse(
                task_id=task.id,
                status=task.status.value,
                message="Export task created",
                output_dir=task.output_dir,
            ))
        except Exception as e:
            responses.append(ExportResponse(
                task_id="error",
                status="failed",
                message=f"Failed to create task for {url}: {str(e)}",
                output_dir=request.output_dir,
            ))
    return responses


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
) -> TaskStatusResponse:
    """Get the status of an export task."""
    try:
        return await task_service.get_task_status(task_id)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/download/{task_id}")
async def download_export(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
):
    """
    Download the exported files for a completed task.

    Returns the files or a zip archive of the export directory.
    """
    try:
        task = await task_service.get_task(task_id)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not task.is_completed:
        raise HTTPException(
            status_code=400,
            detail=f"Task not completed. Status: {task.status.value}"
        )

    if not task.output_path:
        raise HTTPException(status_code=400, detail="No output path found")

    output_path = Path(task.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output path not found")

    if output_path.is_file():
        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type="application/octet-stream"
        )
    else:
        # Return directory listing
        files = []
        for f in output_path.rglob("*"):
            if f.is_file():
                rel_path = f.relative_to(output_path.parent)
                files.append(str(rel_path))
        return {
            "task_id": task_id,
            "output_dir": str(output_path),
            "files": files,
        }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/platforms", response_model=list[PlatformInfo])
async def list_platforms() -> list[PlatformInfo]:
    """List configured parser platforms."""
    return [PlatformInfo(**item) for item in ParserRegistry.available_platforms()]


@router.get("/config", response_model=ExportConfigResponse)
async def get_export_config() -> ExportConfigResponse:
    """Return runtime configuration used by the visual page and API clients."""
    return ExportConfigResponse(
        app_name=settings.app_name,
        display_name="聊两毛的",
        english_name="chat to markdown",
        output_dir=str(settings.output_dir),
        default_options=ExportOptionsSchema(),
        platforms=[PlatformInfo(**item) for item in ParserRegistry.available_platforms()],
    )
