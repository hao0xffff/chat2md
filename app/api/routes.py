"""API routes for the export service."""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
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
    AuthConfigResponse,
    IntegrationExampleResponse,
    MCPStatusResponse,
    MCPToolInfo,
    PlatformInfo,
    StorageConfigResponse,
    SwaggerInfoResponse,
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


def _swagger_info() -> SwaggerInfoResponse:
    """Return public Swagger/OpenAPI endpoints."""
    return SwaggerInfoResponse(
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        title=settings.app_name,
        version=settings.app_version,
    )


def _storage_config() -> StorageConfigResponse:
    """Return runtime storage configuration."""
    return StorageConfigResponse(
        backend=settings.storage_backend,
        output_dir=str(settings.output_dir),
        local_output_dir=str(settings.local_output_dir) if settings.local_output_dir else None,
        allow_custom_output_dir=settings.allow_custom_output_dir,
        object_storage_bucket=settings.object_storage_bucket,
        object_storage_prefix=settings.object_storage_prefix,
        object_storage_endpoint=settings.object_storage_endpoint,
        object_storage_region=settings.object_storage_region,
        access_key_env=settings.object_storage_access_key_env,
        secret_key_env=settings.object_storage_secret_key_env,
    )


def _auth_config() -> AuthConfigResponse:
    """Return deployment auth metadata."""
    return AuthConfigResponse(
        mode=settings.auth_mode,
        sso_provider=settings.sso_provider,
        sso_login_url=settings.sso_login_url,
    )


def _mcp_status() -> MCPStatusResponse:
    """Return MCP status metadata without starting a separate transport."""
    cwd = str(Path.cwd())
    tools = [
        MCPToolInfo(
            name="export_chat_to_markdown",
            description="Export one AI chat share link to an AI-readable Markdown bundle.",
            required=["url"],
        ),
        MCPToolInfo(
            name="get_export_status",
            description="Get the status of an export task.",
            required=["task_id"],
        ),
        MCPToolInfo(
            name="list_supported_platforms",
            description="List currently enabled and registered parser platforms.",
            required=[],
        ),
    ]
    return MCPStatusResponse(
        enabled=True,
        server_name="chat-to-markdown",
        transport="stdio",
        command="python",
        args=["-m", "app.mcp.server"],
        cwd=cwd,
        tools=tools,
    )


def _integration_examples() -> IntegrationExampleResponse:
    """Build copyable integration examples."""
    cwd = str(Path.cwd()).replace("\\", "/")
    return IntegrationExampleResponse(
        swagger=_swagger_info(),
        mcp=_mcp_status(),
        curl_single_export=(
            "curl -X POST http://localhost:8000/api/v1/export "
            "-H \"Content-Type: application/json\" "
            "-d '{\"url\":\"https://chatgpt.com/share/xxx\",\"format\":\"ai_readable\"}'"
        ),
        curl_batch_export=(
            "curl -X POST http://localhost:8000/api/v1/export/batch "
            "-H \"Content-Type: application/json\" "
            "-d '{\"urls\":[\"https://chatgpt.com/share/xxx\",\"https://gemini.google.com/share/yyy\"]}'"
        ),
        mcp_config_json={
            "mcpServers": {
                "chat-to-markdown": {
                    "command": "python",
                    "args": ["-m", "app.mcp.server"],
                    "cwd": cwd,
                }
            }
        },
        python_example=(
            "import httpx\n\n"
            "payload = {\"url\": \"https://chatgpt.com/share/xxx\", \"format\": \"ai_readable\"}\n"
            "response = httpx.post(\"http://localhost:8000/api/v1/export\", json=payload)\n"
            "print(response.json())\n"
        ),
    )


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


@router.get("/swagger", response_model=SwaggerInfoResponse, tags=["integration"])
async def get_swagger_info() -> SwaggerInfoResponse:
    """Return Swagger/OpenAPI URLs."""
    return _swagger_info()


@router.get("/storage", response_model=StorageConfigResponse, tags=["integration"])
async def get_storage_config() -> StorageConfigResponse:
    """Return storage configuration."""
    return _storage_config()


@router.get("/mcp/status", response_model=MCPStatusResponse, tags=["integration"])
async def get_mcp_status() -> MCPStatusResponse:
    """Return MCP server status and tool metadata."""
    return _mcp_status()


@router.get("/integration", response_model=IntegrationExampleResponse, tags=["integration"])
async def get_integration_examples() -> IntegrationExampleResponse:
    """Return copyable API and MCP integration examples."""
    return _integration_examples()


@router.get("/config", response_model=ExportConfigResponse)
async def get_export_config() -> ExportConfigResponse:
    """Return runtime configuration used by the visual page and API clients."""
    return ExportConfigResponse(
        app_name=settings.app_name,
        display_name=settings.display_name,
        english_name=settings.english_name,
        output_dir=str(settings.output_dir),
        swagger=_swagger_info(),
        storage=_storage_config(),
        auth=_auth_config(),
        default_options=ExportOptionsSchema(),
        platforms=[PlatformInfo(**item) for item in ParserRegistry.available_platforms()],
    )
