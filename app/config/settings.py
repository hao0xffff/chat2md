"""Application settings using pydantic-settings."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "chat2md"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Paths
    output_dir: Path = Path("output")
    static_dir: Path = Path("static")
    templates_dir: Path = Path("templates")

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # HTTP Client
    http_timeout: int = 30
    http_max_connections: int = 100
    http_max_keepalive: int = 30

    # Download
    max_concurrent_downloads: int = 10
    download_timeout: int = 60
    max_file_size: int = 50 * 1024 * 1024  # 50MB

    # Export
    markdown_code_fence: str = "```"
    markdown_image_prefix: str = "images"

    # Parser
    parser_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    parser_timeout: int = 30

    # CORS
    cors_origins: list[str] = ["*"]


settings = Settings()