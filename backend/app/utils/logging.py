"""
Financial Intelligence Platform — Structured Logging

Every log line in the system is structured JSON with automatic context:
- trace_id: Request trace ID for end-to-end tracing
- service: Which service/module emitted the log
- user_id: Authenticated user (if applicable)
- timestamp: ISO-8601 with timezone

NO print() statements anywhere. This is non-negotiable.
"""

import sys
import uuid
from contextvars import ContextVar
from typing import Any

from loguru import logger

# Context variables for request-scoped data
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
_service_name: ContextVar[str] = ContextVar("service_name", default="app")


def get_trace_id() -> str:
    """Get current trace ID from context."""
    return _trace_id.get()


def set_trace_id(trace_id: str | None = None) -> str:
    """Set trace ID in context. Generates new one if not provided."""
    tid = trace_id or str(uuid.uuid4())[:8]
    _trace_id.set(tid)
    return tid


def set_user_id(user_id: str | None) -> None:
    """Set user ID in context."""
    _user_id.set(user_id)


def set_service_name(name: str) -> None:
    """Set service name in context."""
    _service_name.set(name)


def _structured_format(record: dict) -> str:
    """Format log record as structured JSON."""
    import orjson

    log_entry: dict[str, Any] = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "level": record["level"].name,
        "service": _service_name.get(),
        "trace_id": _trace_id.get() or None,
        "user_id": _user_id.get(),
        "message": record["message"],
    }

    # Add extra data if present
    if record.get("extra"):
        extra = {k: v for k, v in record["extra"].items()
                 if k not in ("_structured",)}
        if extra:
            log_entry["data"] = extra

    # Add exception info if present
    if record.get("exception"):
        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
        }

    return orjson.dumps(log_entry).decode() + "\n"


def setup_logging(
    level: str = "INFO",
    service_name: str = "app",
    json_output: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        service_name: Name of the service for log context
        json_output: If True, output JSON. If False, output human-readable.
    """
    # Remove default loguru handler
    logger.remove()

    set_service_name(service_name)

    if json_output:
        logger.add(
            sys.stdout,
            format=_structured_format,
            level=level,
            serialize=False,
            colorize=False,
        )
    else:
        # Human-readable format for development
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[service]}</cyan> | "
                "<white>{message}</white>"
            ),
            level=level,
            colorize=True,
        )

    logger.info(
        "Logging initialized",
        service=service_name,
        level=level,
        json_output=json_output,
    )


def get_logger(module_name: str = "") -> logger.__class__:
    """
    Get a contextualized logger for a specific module.

    Usage:
        log = get_logger(__name__)
        log.info("Filing ingested", company_id="AAPL", filing_type="10-Q")
    """
    return logger.bind(module=module_name)
