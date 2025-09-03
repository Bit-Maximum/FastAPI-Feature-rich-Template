from uuid import UUID

from loguru import logger
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.api.dummy.schema import DummyCreate, DummyDataResponse, DummyUpdate
from app.db.dao.base import Filter
from app.db.dao.dummy_dao import dummy_dao
from app.db.exceptions import ElementNotFoundError
from app.services.dummy.mapper import to_model, to_response
from app.services.exeptions import DummyServiceError


class DummyService:
    """Defines the application service for the Dummy services."""

    @staticmethod
    async def delete_dummy(db_connection: AsyncSession, dummy_id: UUID4) -> None:
        """Deletes a dummy object from the database.

        Args:
            db_connection (Session): Database connection.
            dummy_id (UUID4): Dummy ID.

        Raises:
            DummyServiceException: If an error occurs while deleting the dummy.
        """
        try:
            logger.info(f"Deleting dummy with ID: {dummy_id}.")
            db_dummy = await dummy_dao.get_by_id(db_connection, dummy_id)
            await dummy_dao.delete_row(db_connection, db_dummy)
        except ElementNotFoundError:
            logger.error(f"Dummy with ID: {dummy_id} not found.")
            raise
        except Exception as error:
            logger.exception(f"An error occurred while deleting the dummy with ID: {dummy_id}.")
            raise DummyServiceError from error

    @staticmethod
    async def get_dummies(
        db_connection: AsyncSession,
        limit: int,
        offset: int,
        name: str | None,
        dummy_id: str | None,
    ) -> tuple[list[DummyDataResponse], int]:
        """Retrieve a paginated list of dummies with optional filtering.

        Args:
            db_connection (AsyncSession): Database connection.
            limit (int): Number of items to retrieve.
            offset (int): Items to skip for pagination.
            name (str | None): Optional filter by name.
            dummy_id (str | None): Optional filter by ID.

        Returns:
            tuple[list[DummyDataResponse], int]: A list of dummies and their total count.

        Raises:
            DummyServiceError: If a database or processing error occurs.
        """
        try:
            filters = []
            if name:
                filters.append(Filter(field="name", operator="contains", value=name))
            if dummy_id:
                filters.append(Filter(field="dummy_id", operator="eq", value=dummy_id))

            logger.debug(f"Filters: {filters}")

            db_data = await dummy_dao.get_list(
                db_connection,
                offset,
                limit,
                filters,
            )
            logger.debug(f"Data retrieved: {db_data}")
            response_data = [
                DummyDataResponse(
                    dummyId=str(row.id),
                    name=row.name,
                )
                for row in db_data
            ]
            db_count = len(db_data)
            logger.debug(f"Response data: {response_data}\nTotal count: {db_count}")

        except ElementNotFoundError:
            logger.error("No dummy found.")
            return [], 0
        except Exception as error:
            logger.exception("An error occurred while retrieving the dummies.")
            raise DummyServiceError from error
        else:
            return response_data, db_count

    @staticmethod
    async def get_dummy_id(db_connection: AsyncSession, dummy_id: UUID4) -> DummyDataResponse:
        """Retrieve a specific dummy by its ID.

        Args:
            db_connection (AsyncSession): Database connection.
            dummy_id (UUID4): Dummy object ID.

        Returns:
            DummyDetailResponse: Details of the dummy object.

        Raises:
            ElementNotFoundError: If the dummy does not exist.
            DummyServiceError: For other database or processing errors.
        """
        try:
            logger.debug(f"Requesting a Dummy with ID: {dummy_id}")
            db_data = await dummy_dao.get_by_id(db_connection, dummy_id)
            logger.debug(f"Data retrieved: {db_data}")
            api_data = to_response(db_data)
            logger.debug(f"Response data: {api_data}")

        except ElementNotFoundError:
            logger.error(f"Dummy with ID '{dummy_id}' not found.")
            raise
        except Exception as error:
            logger.exception("An error occurred while retrieving the dummy.")
            raise DummyServiceError from error
        else:
            return api_data

    @staticmethod
    async def post_dummy(db_connection: AsyncSession, dummy: DummyCreate) -> UUID:
        """Create a new dummy object in the database.

        Args:
            db_connection (AsyncSession): Database connection.
            dummy (DummyCreate): Data for the new dummy.

        Returns:
            UUID: The unique identifier of the created dummy.

        Raises:
            DummyServiceError: If creation fails.
        """
        try:
            db_dummy = to_model(dummy)
            await dummy_dao.create(db_connection, db_dummy)
            logger.debug(f"Customer created: {db_dummy}")
            return UUID(str(db_dummy.id))
        except Exception as error:
            logger.exception("An error occurred while creating the dummy.")
            raise DummyServiceError from error

    @staticmethod
    async def put_dummy(db_connection: AsyncSession, dummy_id: UUID4, dummy: DummyUpdate) -> None:
        """Update the details of an existing dummy.

        Args:
            db_connection (AsyncSession): Database connection.
            dummy_id (UUID4): Dummy object ID to update.
            dummy (DummyUpdate): New data for the dummy.

        Raises:
            ElementNotFoundError: If the dummy does not exist.
            DummyServiceError: For other database or processing errors.
        """
        try:
            db_dummy = await dummy_dao.get_by_id(db_connection, dummy_id)
            logger.debug(f"Dummy retrieved: {db_dummy}")
            if dummy.name:
                db_dummy.name = dummy.name
                await dummy_dao.update(db_connection, db_dummy)
                logger.debug(f"Dummy updated: {db_dummy}")
        except ElementNotFoundError:
            logger.error(f"Dummy with ID '{dummy_id}' not found.")
            raise
        except Exception as error:
            logger.exception("An error occurred while updating the dummy.")
            raise DummyServiceError from error
