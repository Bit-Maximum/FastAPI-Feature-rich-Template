import logging
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.core.logger import configure_logging
from app.web.api.router import api_router
from app.web.lifespan import lifespan_setup

APP_ROOT = Path(__file__).parent.parent


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    configure_logging()
    if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
        # Enables sentry integration.
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            send_client_reports=settings.SENTRY_ALLOW_BEACON_REPORTS,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            environment=settings.ENVIRONMENT,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.getLevelName(
                        settings.LOG_LEVEL.value,
                    ),
                    event_level=logging.ERROR,
                ),
                SqlalchemyIntegration(),
            ],
            _experiments={"metrics": False},
        )
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        contact={
            "name": settings.CONTACT_NAME,
            "email": settings.CONTACT_EMAIL,
        },
        lifespan=lifespan_setup,
        docs_url=f"{settings.API_BASE_PATH}/docs",
        redoc_url=f"{settings.API_BASE_PATH}/redoc",
        openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
        default_response_class=ORJSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["X-Requested-With", "X-Request-ID", "Content-Type"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # Main router for the API.
    app.include_router(router=api_router, prefix=settings.API_BASE_PATH)

    # Adds static directory.
    # This directory is used to access swagger files.
    app.mount(
        f"{settings.API_BASE_PATH}",
        StaticFiles(directory=APP_ROOT / "static"),
        name="static",
    )

    return app
