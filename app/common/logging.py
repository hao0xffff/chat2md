"""Logging configuration using structlog."""
import logging
import sys
from typing import Any

import structlog

from app.config.settings import settings


def configure_logging() -> None:
    """Configure structlog for the application."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **kwargs: Any) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Optional logger name (component name).
        **kwargs: Additional context to bind to the logger.

    Returns:
        A configured BoundLogger instance.
    """
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(component=name)
    if kwargs:
        logger = logger.bind(**kwargs)
    return logger