"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router
from app.api.dependencies import container
from app.common.logging import configure_logging, get_logger
from app.common.utils import ensure_dir
from app.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    configure_logging()
    logger = get_logger("startup")
    logger.info("application_starting", version=settings.app_version)

    # Ensure directories exist
    ensure_dir(settings.output_dir)
    ensure_dir(settings.static_dir)
    ensure_dir(settings.templates_dir)

    yield

    # Shutdown
    logger.info("application_stopping")
    # Close HTTP client
    await container.http_client().close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Conversation Export System - Export chat sessions to Markdown",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes with /api/v1 prefix
    app.include_router(router)

    # Static files
    if settings.static_dir.exists():
        app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    # Templates
    templates = Jinja2Templates(directory=settings.templates_dir)

    # Root web interface
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return templates.TemplateResponse("index.html", {"request": {}})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )