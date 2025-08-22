import os
import shutil
from pathlib import Path

import uvicorn

from app.core.config import settings


def set_multiproc_dir() -> None:
    """
    Sets mutiproc_dir env variable.

    This function cleans up the multiprocess directory
    and recreates it. Thous actions are required by prometheus-client
    to share metrics between processes.

    After cleanup, it sets two variables.
    Uppercase and lowercase because different
    versions of the prometheus-client library
    depend on different environment variables,
    so I've decided to export all needed variables,
    to avoid undefined behaviour.
    """
    shutil.rmtree(settings.PROMETHEUS_DIR, ignore_errors=True)
    Path(settings.PROMETHEUS_DIR).mkdir(parents=True)
    os.environ["prometheus_multiproc_dir"] = str(  # noqa: SIM112
        settings.PROMETHEUS_DIR.expanduser().absolute(),
    )
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(
        settings.PROMETHEUS_DIR.expanduser().absolute(),
    )


def main() -> None:
    """Entrypoint of the application."""
    set_multiproc_dir()
    uvicorn.run(
        "app.web.application:get_app",
        workers=settings.UVICORN_WORKERS_COUNT,
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.UVICORN_RELOAD,
        log_level=settings.LOG_LEVEL.value.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
