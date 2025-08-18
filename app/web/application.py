import logging
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.cors import CORSMiddleware

from app.log import configure_logging
from app.settings import settings
from app.web.api.router import api_router
from app.web.lifespan import lifespan_setup

APP_ROOT = Path(__file__).parent.parent


def custom_generate_unique_id(route: APIRoute) -> str:
    """
    Generate a unique operation ID for FastAPI routes based on their tag and name.

    :param route: The APIRoute instance to generate the ID for.
    :return: Unique string combining the route's tag and name.
    """
    return f"{route.tags[0]}-{route.name}"


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
        docs_url=f"{settings.API_BASE_PATH}/swagger",
        redoc_url=f"{settings.API_BASE_PATH}/redoc",
        openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
        default_response_class=ORJSONResponse,
        generate_unique_id_function=custom_generate_unique_id,
    )

    # Set all CORS enabled origins
    if settings.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Main router for the API.
    app.include_router(router=api_router, prefix=settings.API_BASE_PATH)
    # Adds static directory.
    # This directory is used to access swagger files.
    app.mount(
        f"/{settings.API_BASE_PATH}",
        StaticFiles(directory=APP_ROOT / f"{settings.API_BASE_PATH}"),
        name="static",
    )

    return app
