import logging
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger
from opentelemetry.trace import INVALID_SPAN, INVALID_SPAN_CONTEXT, get_current_span

from app.core.config import LogLevel, settings


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.

    This handler intercepts all log requests and
    passes them to loguru.

    For more info see:
    https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        """
        Propagates logs to loguru.

        :param record: record to log.
        """
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def record_formatter(record: dict[str, Any]) -> str:  # pragma: no cover
    """
    Formats the record.

    This function formats message
    by adding extra trace information to the record.

    :param record: record information.
    :return: format string.
    """
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
        "| <level>{level: <8}</level> "
        "| <magenta>trace_id={extra[trace_id]}</magenta> "
        "| <blue>span_id={extra[span_id]}</blue> "
        "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>\n"
    )

    # OpenTelemetry trace/span
    span = get_current_span()
    record["extra"]["span_id"] = 0
    record["extra"]["trace_id"] = 0
    if span != INVALID_SPAN:
        span_context = span.get_span_context()
        if span_context != INVALID_SPAN_CONTEXT:
            record["extra"]["span_id"] = format(span_context.span_id, "016x")
            record["extra"]["trace_id"] = format(span_context.trace_id, "032x")

    if record["exception"]:
        log_format = f"{log_format}{{exception}}"

    return log_format


def cleanup_old_logs(log_directory: Path, retention_days: int = 7) -> None:
    """Remove log files older than a specified number of days."""
    threshold = datetime.now(UTC) - timedelta(days=retention_days)
    for log_file in log_directory.glob("*.log"):
        try:
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime, tz=UTC)
            if file_time < threshold:
                log_file.unlink()
                logger.info(f"Deleted old log file: {log_file}")
        except OSError as error:
            logger.exception(f"Failed to delete old log file {log_file}: {error}")


def configure_logging() -> None:  # pragma: no cover
    """Configures logging."""
    intercept_handler = InterceptHandler()

    logging.basicConfig(handlers=[intercept_handler], level=logging.NOTSET)

    log_level = (
        LogLevel.DEBUG if settings.ENVIRONMENT in ["debug", "pytest"] else settings.LOG_LEVEL
    )

    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("uvicorn."):
            logging.getLogger(logger_name).handlers = []
        if logger_name.startswith("taskiq."):
            logging.getLogger(logger_name).root.handlers = [intercept_handler]

    # change handler for default uvicorn logger
    logging.getLogger("uvicorn").handlers = [intercept_handler]
    logging.getLogger("uvicorn.access").handlers = [intercept_handler]

    # Remove default loguru handlers
    logger.remove()

    # Console handler
    logger.add(
        sys.stdout,
        level=log_level,
        format=record_formatter,
        enqueue=True,
    )

    # Determine log file path
    log_file_path = Path(settings.LOG_FILE_PATH).resolve()

    if not log_file_path.parent.exists():
        log_file_path.parent.mkdir(parents=True)
    if not log_file_path.exists():
        log_file_path.touch()

    # Calculate the maximum log file size (15% of disk capacity or 4GB, whichever is smaller)
    max_log_size = min(
        0.15 * shutil.disk_usage(log_file_path.parent).total,
        4 * 1024 * 1024 * 1024,
    )

    logger.add(
        log_file_path,
        rotation=int(max_log_size),
        retention="7 days",
        compression="zip",
        level=log_level,
        format=record_formatter,
        enqueue=True,
    )


if __name__ == "__main__":
    configure_logging()
    logger.debug("Debug log")
    logger.info("Info log with cid + tracing")
    logger.warning("Warning log")
    logger.error("Error log")
    logger.critical("Critical log")
    cleanup_old_logs(Path(settings.LOG_FILE_PATH).parent, retention_days=7)
