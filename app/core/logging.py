import contextvars
import logging
import sys

from pythonjsonlogger.json import JsonFormatter

# Context variable to hold request_id across async tasks
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="system")


class CorrelationIdFilter(logging.Filter):
    """Logging filter that injects the current correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging for the application and uvicorn loggers."""
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"

    formatter = JsonFormatter(
        log_format,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Align uvicorn and app loggers
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "app"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False
