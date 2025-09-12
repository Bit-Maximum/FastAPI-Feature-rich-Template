from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse, Response
from loguru import logger
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.api.v1.dummy.schema import (
    DummyCreate,
    DummyDataResponse,
    DummyListResponse,
    DummyUpdate,
)
from app.controller.api.v1.errors.deps import compose_responses
from app.controller.errors.exceptions import HTTP404NotFoundError, HTTP500InternalServerError
from app.controller.utils.pagination import MAX_LIMIT, MAX_OFFSET, Pagination
from app.controller.utils.query_parameters import common_query_parameters
from app.db.dependencies import get_db_session
from app.db.exceptions import ElementNotFoundError
from app.services.dummy.service import DummyService

ROUT_TAGS = ["Dummy"]

router = APIRouter()

CommonDeps = Annotated[dict[str, Any], Depends(common_query_parameters)]


@router.get(
    "/",
    responses=compose_responses({200: {"model": DummyListResponse, "description": "OK."}}),
    tags=ROUT_TAGS,
    summary="List of Dummy models.",
    response_model_by_alias=True,
    response_model=DummyListResponse,
)
async def get_dummies(
    request: Request,
    http_request_info: CommonDeps,
    db_connection: Annotated[AsyncSession, Depends(get_db_session)],
    name: Annotated[str | None, Query(description="Filter dummies by name.")] = None,
    dummy_id: Annotated[int | None, Query(description="Filter dummies by ID.")] = None,
    limit: Annotated[
        int,
        Query(
            description="Number of records returned per page."
            " If specified on entry, this will be the value of the query,"
            " otherwise it will be the value value set by default.",
            ge=1,
            le=MAX_LIMIT,
        ),
    ] = 10,
    offset: Annotated[
        int,
        Query(
            description="Record number from which you want to receive"
            " the number of records indicated in the limit."
            " If it is indicated at the entry, it will be the value of the query."
            " If it is not indicated at the input, as the query is on the first page,"
            " its value will be 0.",
            ge=0,
            le=MAX_OFFSET,
        ),
    ] = 0,
) -> JSONResponse:
    """
    Retrieve a paginated list of dummy models, optionally filtered by name or ID.

    Args:
        request: The current HTTP request.
        http_request_info: Common HTTP headers.
        db_connection: SQLAlchemy async session.
        name: Optional; filter by dummy name.
        dummy_id: Optional; filter by dummy ID.
        limit: Pagination size.
        offset: Pagination offset.

    Returns:
        JSONResponse: List of dummies with pagination metadata.

    Raises:
        HTTP500InternalServerError: If database access fails.
    """
    logger.info(logger.info("Entering..."))
    try:
        response_data, db_count = await DummyService.get_dummies(
            db_connection=db_connection, limit=limit, offset=offset, name=name, dummy_id=dummy_id
        )
        logger.debug("Dummies retrieved.")
    except Exception as error:
        logger.exception(f"Error getting dummies: {error}")
        raise HTTP500InternalServerError from error

    pagination = Pagination.get_pagination(
        offset=offset,
        limit=limit,
        total_elements=db_count,
        url=str(request.url),
    )
    response = DummyListResponse(data=response_data, pagination=pagination)
    logger.info("Exiting...")
    return JSONResponse(
        content=response.model_dump(), status_code=status.HTTP_200_OK, headers=http_request_info
    )


@router.post(
    "/",
    responses=compose_responses({201: {"description": "Created."}}),
    tags=ROUT_TAGS,
    summary="Create a new dummy.",
    response_model_by_alias=True,
)
async def post_dummy(
    request: Request,
    http_request_info: CommonDeps,
    db_connection: Annotated[AsyncSession, Depends(get_db_session)],
    dummy_body: Annotated[DummyCreate, Body()],
) -> Response:
    """
    Create a new dummy model.

    Args:
        request: The HTTP request.
        http_request_info: Common HTTP headers.
        db_connection: SQLAlchemy async session.
        dummy_body: DummyCreate schema instance.

    Returns:
        Response: 201 Created with location header of the new resource.

    Raises:
        HTTP500InternalServerError: If creation fails.
    """
    logger.info("Entering...")
    try:
        dummy_id = await DummyService.post_dummy(
            db_connection,
            dummy_body,
        )
        logger.debug(f"Created dummy ID: {dummy_id}")
    except Exception as error:
        logger.exception("Error creating a dummy.")
        raise HTTP500InternalServerError from error

    # Merge standard headers with dynamic location for resource creation
    headers = http_request_info | {
        "location": f"{request.url.scheme}://{request.url.netloc}/dummy/{dummy_id}",
    }
    logger.info("Exiting...")
    return Response(status_code=status.HTTP_201_CREATED, headers=headers)


@router.put(
    "/{dummy_id}",
    responses=compose_responses({204: {"description": "No Content."}}),
    tags=ROUT_TAGS,
    summary="Update information from a dummy.",
    response_model_by_alias=True,
)
async def put_dummy_with_id(
    dummy_id: Annotated[UUID4, Path(description="Id of a specific dummy.")],
    http_request_info: CommonDeps,
    db_connection: Annotated[AsyncSession, Depends(get_db_session)],
    dummy_body: Annotated[DummyUpdate, Body()],
) -> Response:
    """
    Update a dummy model by its UUID.

    Args:
        dummy_id: UUID4 of the dummy.
        http_request_info: Common HTTP headers.
        db_connection: SQLAlchemy async session.
        dummy_body: Update data.

    Returns:
        Response: 204 No Content on success.

    Raises:
        HTTP404NotFoundError: If the dummy does not exist.
        HTTP500InternalServerError: On other failures.
    """
    logger.info("Entering...")
    try:
        await DummyService.put_dummy(
            db_connection,
            dummy_id,
            dummy_body,
        )
        logger.debug(f"Updated dummy with ID: {dummy_id}")

    except ElementNotFoundError as error:
        logger.exception(f"Dummy with id={dummy_id} not found")
        raise HTTP404NotFoundError from error

    except Exception as error:
        logger.exception(f"Error updating dummy with ID {dummy_id}.")
        raise HTTP500InternalServerError from error
    logger.info("Exiting...")
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=http_request_info)


@router.delete(
    "/{dummy_id}",
    responses=compose_responses({204: {"description": "No Content."}}),
    tags=ROUT_TAGS,
    summary="Delete specific dummy.",
    response_model=None,
)
async def delete_dummy(
    dummy_id: Annotated[UUID4, Path(description="Id of a specific dummy.")],
    http_request_info: CommonDeps,
    db_connection: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """
    Delete a dummy model by UUID.

    Args:
        dummy_id: UUID4 of the dummy.
        http_request_info: Common HTTP headers.
        db_connection: SQLAlchemy async session.

    Returns:
        Response: 204 No Content.

    Raises:
        HTTP404NotFoundError: If the dummy does not exist.
        HTTP500InternalServerError: On other failures.
    """
    logger.info("Entering...")
    try:
        await DummyService.delete_dummy(
            db_connection,
            dummy_id,
        )
        logger.debug(f"Deleted dummy with ID: {dummy_id}")

    except ElementNotFoundError as error:
        logger.exception(f"Dummy with id={dummy_id} not found")
        raise HTTP404NotFoundError from error

    except Exception as error:
        logger.exception(f"Error deleting dummy with ID {dummy_id}.")
        raise HTTP500InternalServerError from error
    logger.info("Exiting...")
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=http_request_info)


@router.get(
    "{dummy_id}",
    responses=compose_responses({200: {"model": DummyDataResponse, "description": "OK."}}),
    tags=ROUT_TAGS,
    summary="Get a dummy.",
    response_model=DummyDataResponse,
    response_model_by_alias=True,
)
async def get_dummy(
    dummy_id: Annotated[UUID4, Path(description="Id of a specific dummy.")],
    http_request_info: CommonDeps,
    db_connection: Annotated[AsyncSession, Depends(get_db_session)],
) -> JSONResponse:
    """
    Retrieve a single dummy by UUID.

    Args:
        dummy_id: UUID4 of the dummy.
        http_request_info: Common HTTP headers.
        db_connection: SQLAlchemy async session.

    Returns:
        JSONResponse: Dummy model.

    Raises:
        HTTP404NotFoundError: If not found.
        HTTP500InternalServerError: On unexpected error.
    """
    logger.info("Entering...")
    try:
        api_data = await DummyService.get_dummy_id(db_connection, dummy_id)
        logger.debug(f"Retrieved dummy with ID: {dummy_id}")

    except ElementNotFoundError as error:
        logger.exception(f"Dummy with id={dummy_id} not found")
        raise HTTP404NotFoundError from error

    except Exception as error:
        logger.exception(f"Error retrieving dummy with ID {dummy_id}.")
        raise HTTP500InternalServerError from error

    logger.info("Exiting...")
    return JSONResponse(
        content=api_data.model_dump(), status_code=status.HTTP_200_OK, headers=http_request_info
    )
