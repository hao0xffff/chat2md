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
    app_name: str = "chat-to-markdown"
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
    http_proxy: str | None = None
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
    default_export_format: str = "ai_readable"
    default_include_images: bool = True
    default_include_metadata: bool = True
    default_include_frontmatter: bool = True
    default_create_index: bool = True
    default_create_manifest: bool = True
    default_create_messages: bool = True

    # Parser
    parser_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    parser_timeout: int = 30
    enabled_platforms: list[str] = ["chatgpt", "gemini"]
    platform_url_patterns: dict[str, list[str]] = {
        "chatgpt": ["chatgpt.com/share"],
        "gemini": ["gemini.google.com/share", "g.co/gemini/share"],
        "doubao": ["doubao.com/share", "www.doubao.com/share"],
    }

    # CORS
    cors_origins: list[str] = ["*"]


settings = Settings()
