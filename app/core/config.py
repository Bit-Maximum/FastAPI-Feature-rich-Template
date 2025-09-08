"""File with environment variables and general configuration logic.

`SECRET_KEY`, `ENVIRONMENT` etc. map to env variables with the same names.

Pydantic priority ordering:

1. If cli_parse_args is enabled, arguments passed in at the CLI.
2. Arguments passed to the Settings class initialiser.
3. Environment variables.
4. Variables loaded from a dotenv (.env) file.
5. Variables loaded from the secrets directory.
6. The default field values for the Settings model.

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
from typing import Literal

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

    # Configuration for the settings class
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", env_file_encoding="utf-8", extra="ignore"
    )

    # CORE SETTINGS
    SECRET_KEY: str = ""
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FILE_PATH: str = "logs/app.log"
    USERS_SECRET: str = ""
    ENVIRONMENT: Literal["debug", "local", "pytest", "staging", "production"] = "local"
    ## CORS_ORIGINS and ALLOWED_HOSTS are a JSON-formatted list of origins
    ## For example: ["http://localhost:4200", "https://myfrontendapp.com"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "api.localhost"]
    CORS_ORIGINS: list[str] = ["localhost", "127.0.0.1"]

    APP_LOG_FILE_PATH: str = "logs/app.log"
    API_BASE_PATH: str = "/api"
    APP_VERSION: str = "latest"
    APP_HOST: str = "0.0.0.0"

    # Docker adapters` hosts
    API_CONTAINER_HOST: str = "app-api"
    API_TASKIQ_CONTAINER_HOST: str = "api-taskiq"
    DB_CONTAINER_HOST: str = "app-db"
    REDIS_CONTAINER_HOST: str = "app-redis"
    RABBITMQ_CONTAINER_HOST: str = "app-rmq"
    KAFKA_CONTAINER_HOST: str = "app-kafka"

    # Emails
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587

    # Uvicorn
    UVICORN_HOST: str = "127.0.0.1"
    UVICORN_PORT: int = 8000
    UVICORN_WORKERS_COUNT: int = 1
    UVICORN_RELOAD: bool = True

    # Variables for the database
    DB_HOST: str = "db"  # The name of the service in the docker-compose file
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = ""
    DB_NAME: str = "app"
    DB_ECHO: bool = False
    DB_ECHO_POOL: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # SQLAlchemy engine settings
    # The size of the pool to be maintained, defaults to 10
    # See: https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.pool_size
    CONNECTION_POOL_SIZE: int = 10
    # Controls the number of connections that can be created after the pool reached its size
    # See: https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.max_overflow
    CONNECTION_MAX_OVERFLOW: int = 20
    # Number of seconds to wait before giving up on getting a connection from the pool
    # See: https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.pool_timeout
    CONNECTION_POOL_TIMEOUT: int = 30
    # Number of seconds after which a connection is recycled (preventing stale connections)
    # See: https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.pool_recycle
    CONNECTION_POOL_RECYCLE: int = 1800
    # Enable feature that tests connections for liveness upon each checkout.
    # See: https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.pool_pre_ping
    CONNECTION_POOL_PRE_PING: bool = True

    # Variables for Redis
    REDIS_HOST: str = "app-redis"  # The name of the service in the docker-compose file
    REDIS_PORT: int = 6379
    REDIS_USER: str | None = None
    REDIS_PASS: str | None = None
    REDIS_DATABASE: str | None = None

    # Variables for RabbitMQ
    RABBITMQ_HOST: str = "app-rmq"  # The name of the service in the docker-compose file
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = ""
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_POOL_SIZE: int = 2
    RABBITMQ_CHANNEL_POOL_SIZE: int = 10

    # This variable is used to define
    # multiproc_dir. It's required for [uvi|guni]corn projects.
    PROMETHEUS_MULTIPROC_DIR: Path = TEMP_DIR / "prom"

    # Sentry's configuration.
    SENTRY_DSN: str | None = None
    SENTRY_ALLOW_BEACON_REPORTS: bool = False
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1

    # Grpc endpoint for opentelemetry.
    # E.G. http://localhost:4317
    OPENTELEMETRY_ENDPOINT: str | None = None

    KAFKA_ADDR: list[str] = ["app-kafka:9092"]

    # Additional Project Settings
    BASE_API_PATH: str = "/api"
    API_VERSION: str = "1.0.0"
    PROJECT_NAME: str = "FastAPI Template"
    PROJECT_DESCRIPTION: str = "FastAPI Template"
    CONTACT_NAME: str = "Bit Maximum"
    CONTACT_EMAIL: str = "bit.maximum@email.com"

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.DB_HOST,
            port=self.DB_PORT,
            user=self.DB_USER,
            password=self.DB_PASS,
            path=f"/{self.DB_NAME}",
        )

    @property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = ""
        if self.REDIS_DATABASE is not None:
            path = f"/{self.REDIS_DATABASE}"
        return URL.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            user=self.REDIS_USER,
            password=self.REDIS_PASS,
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
            host=self.RABBITMQ_HOST,
            port=self.RABBITMQ_PORT,
            user=self.RABBITMQ_USER,
            password=self.RABBITMQ_PASS,
            path=self.RABBITMQ_VHOST,
        )


settings = Settings()
