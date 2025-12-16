"""
Logging configuration with structured JSON formatting.

This module provides centralized logging configuration with structured
output for production environments and human-readable output for development.
"""
import datetime
import json
import logging
import sys
from typing import Any

from .config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log entry
        """

        log_data = {
            "timestamp": datetime.datetime.now().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if hasattr(record, "__dict__"):
            standard_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'
            }

            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith('_'):
                    log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)

        return json.dumps(log_data)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for development console output."""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record: logging.LogRecord):
        """
        Format log record with colors for console.

        Args:
            record: Log record to format

        Returns:
            str: Colored log entry
        """
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        timestamp = datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        message = (
            f"{color}[{record.levelname}]{reset} "
            f"{timestamp} "
            f"- {record.name} "
            f"- {record.getMessage()}"
        )

        if hasattr(record, "__dict__"):
            standard_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'
            }

            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in standard_attrs and not k.startswith('_')
            }

            if extra_fields:
                extra_str = " | ".join(f"{k}={v}" for k, v in extra_fields.items())
                message += f" | {extra_str}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging(
    level: str = None,
    json_format: bool = None,
    log_file: str = None
) -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting (default: True for production)
        log_file: Optional file path for log output
    """

    if level is None:
        level = "DEBUG" if settings.DEBUG else "INFO"

    if json_format is None:
        json_format = not settings.DEBUG

    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = ColoredFormatter()


    handlers = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": level,
            "json_format": json_format,
            "environment": settings.ENVIRONMENT
        }
    )


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to all log messages."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Add context to log messages.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            tuple: Processed message and kwargs
        """

        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra

        return msg, kwargs


def get_logger(name: str, **context) ->ContextLogger:
    """
    Get a logger with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all log messages

    Returns:
        ContextLogger: Logger with context

    Example:
        >>> logger = get_logger(__name__, service="file_upload", version="1.0")
        >>> logger.info("File uploaded", extra={"file_id": 123})
    """

    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)

