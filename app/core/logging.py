import structlog
from pydantic_settings import SettingsConfigDict


class LoggingSettings:
    """Logging configuration from environment."""

    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=".env")

    log_level: str = "INFO"
    log_format: str = "json"


def configure_structlog(settings: LoggingSettings) -> None:
    """Configure structlog based on settings."""

    log_processors: list[structlog.processors.Processor] = []

    if settings.log_format == "json":
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(settings.log_level.upper()),
            contextvars_formatter=structlog.contextvars.wrapdict(),
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
                structlog.processors.TimeStamper(fmt="%Y-%m-%dT%H:%M:%S.%z", utc=True),
                structlog.processors.UnicodeEncoder(),
                structlog.processors.JSONRenderer(),
            ],
        )
    else:
        # Development format (human-readable)
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(settings.log_level.upper()),
            contextvars_formatter=structlog.contextvars.wrapdict(),
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )

    __version__ = "fd-open-bench-0.1.0"
