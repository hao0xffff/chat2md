"""Dependency injection container."""
from dependency_injector import containers, providers

from app.application.export_service import ExportService
from app.application.task_service import InMemoryTaskRepository, TaskService
from app.config.settings import settings
from app.infrastructure.client.http_client import HttpClient
from app.infrastructure.downloader.aiohttp_downloader import AiohttpDownloader
from app.infrastructure.exporter.markdown_exporter import MarkdownExporter
from app.infrastructure.repository.file_task_repo import FileTaskRepository
from app.infrastructure.repository.in_memory_conversation_repo import InMemoryConversationRepository
from app.domain.parser.registry import ParserRegistry


def create_task_repository():
    """Create the configured task repository."""
    if settings.task_repository_backend.lower() == "file":
        return FileTaskRepository(settings.task_repository_path)
    return InMemoryTaskRepository()


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the application."""

    # HTTP Client
    http_client = providers.Singleton(HttpClient)

    # Repositories
    conversation_repository = providers.Singleton(InMemoryConversationRepository)
    task_repository = providers.Singleton(create_task_repository)

    # Services
    task_service = providers.Factory(
        TaskService,
        task_repository=task_repository,
    )

    # Infrastructure
    downloader = providers.Factory(
        AiohttpDownloader,
        http_client=http_client,
    )

    exporter = providers.Factory(MarkdownExporter)

    # Application Services
    export_service = providers.Factory(
        ExportService,
        parser_registry=ParserRegistry,
        exporter=exporter,
        downloader=downloader,
        task_repository=task_repository,
    )


container = Container()
