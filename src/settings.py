"""File with environment variables and general configuration logic.

`SECRET_KEY`, `ENVIRONMENT` etc. map to env variables with the same names.

Pydantic priority ordering:

1. (Most important, will overwrite everything) - environment variables
2. `.env` file in root folder of project
3. Default values

For project name, version, description we use pyproject.toml
For the rest, we use file `.env` (gitignored), see `.env.example`

`SQLALCHEMY_DATABASE_URI` is  meant to be validated at the runtime,
do not change unless you know what are you doing.
The validator is to build full URI (TCP protocol) to databases to avoid typo bugs.

See https://pydantic-docs.helpmanual.io/usage/settings/

Note, complex types like lists are read as json-encoded strings.
"""

import enum
from pathlib import Path
from tempfile import gettempdir

from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

TEMP_DIR = Path(gettempdir())


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO

    # Variables for Redis
    redis_host: str = "src-redis"
    redis_port: int = 6379
    redis_user: str | None = None
    redis_pass: str | None = None
    redis_base: int | None = None

    # Variables for RabbitMQ
    rabbit_host: str = "src-rmq"
    rabbit_port: int = 5672
    rabbit_user: str = "guest"
    rabbit_pass: str
    rabbit_vhost: str = "/"

    rabbit_pool_size: int = 2
    rabbit_channel_pool_size: int = 10

    # This variable is used to define
    # multiproc_dir. It's required for [uvi|guni]corn projects.
    prometheus_dir: Path = TEMP_DIR / "prom"

    # Sentry's configuration.
    sentry_dsn: str | None = None
    sentry_sample_rate: float = 1.0

    # Grpc endpoint for opentelemetry.
    # E.G. http://localhost:4317
    opentelemetry_endpoint: str | None = None

    kafka_bootstrap_servers: list[str] = ["src-kafka:9092"]

    @property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = ""
        if self.redis_base is not None:
            path = f"/{self.redis_base}"
        return URL.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            user=self.redis_user,
            password=self.redis_pass,
            path=path,
        )

    @property
    def rabbit_url(self) -> URL:
        """
        Assemble RabbitMQ URL from settings.

        :return: rabbit URL.
        """
        return URL.build(
            scheme="amqp",
            host=self.rabbit_host,
            port=self.rabbit_port,
            user=self.rabbit_user,
            password=self.rabbit_pass,
            path=self.rabbit_vhost,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        env_file_encoding="utf-8",
    )


settings = Settings()
