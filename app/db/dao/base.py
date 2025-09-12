"""Data Access Object with default methods to Create, Read, Update, Delete (CRUD)."""

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from loguru import logger
from pydantic import UUID4, BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm import Query as SQLQuery

from app.db.exceptions import ElementNotFoundError
from app.db.models.base import Base

if TYPE_CHECKING:
    from collections.abc import Callable

ModelType = TypeVar("ModelType", bound=Base)  # pylint: disable=invalid-name


class Filter(BaseModel):
    """Filter to be applied to a query.
    - field: str → name of the models`s column for (example "email".
        Can be nested for relationships: e.g. "address.country").
    - operator: str → one of "eq", "neq", "contains", "gt", "gte", "lt", "lte".
    - value: Any → value to comparison.
    """

    field: str = Field(..., examples=["name"])
    operator: Literal["eq", "neq", "contains", "not_contains", "gt", "gte", "lt", "lte"] = Field(
        ...,
        examples=["eq"],
    )
    value: str | int | float | bool | uuid.UUID = Field(..., examples=["John Doe"])


class DAOBase(Generic[ModelType]):
    """Data Access Object with default methods to Create, Read, Update, Delete (CRUD)."""

    def __init__(self: "DAOBase[ModelType]", model: type[ModelType]) -> None:
        self.model = model

    def _get_filter_expression(self, filter_field: Any, operator: str, value: any) -> SQLQuery:  # noqa: ANN401
        """
        Return the filter expression based on the operator and value.

        Args:
            filter_field: The SQLAlchemy model field to apply the filter on.
            operator: The filter operation to perform (e.g., "eq", "neq").
            value: The value to compare the field against.

        Returns:
            An SQLAlchemy query object representing the filter expression.

        Raises:
            ValueError: If the operator is not supported.
        """
        operators: dict[str, Callable[[any], SQLQuery]] = {
            "eq": lambda f: f == value,
            "neq": lambda f: f != value,
            "contains": lambda f: f.contains(value),
            "not_contains": lambda f: ~f.contains(value),
            "gt": lambda f: f > value,
            "gte": lambda f: f >= value,
            "lt": lambda f: f < value,
            "lte": lambda f: f <= value,
        }

        if operator not in operators:
            msg = f"Operator {operator} not supported."
            raise ValueError(msg)
        return operators[operator](filter_field)

    def _get_filters(self, items: list[Filter]) -> list[SQLQuery]:
        """
        Get the filters to be applied to a query.

        Args:
            items: A list of Filter objects specifying the filters to apply.

        Returns:
            A list of SQLAlchemy query objects representing the filters to be applied.
        """
        filter_clauses = []
        for filter_obj in items:
            field_parts = filter_obj.field.split(".")
            filter_field = getattr(self.model, field_parts[0])

            for part in field_parts[1:]:
                filter_field = getattr(filter_field.property.mapper.class_, part)

            filter_clauses.append(
                self._get_filter_expression(filter_field, filter_obj.operator, filter_obj.value)
            )
        return filter_clauses

    async def get_by_id(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        row_id: int | UUID4,
    ) -> ModelType:
        """Returns an object of the model specified.

        Args:
            db (Session): Database session.
            row_id (int): ID of the row in the DB.

        Returns:
            ModelType: Element.

        Raises:
            ElementNotFoundError: If the element is not found.
        """
        logger.debug(f"Getting {self.model.__name__} with ID: {row_id}")
        query = select(self.model).where(self.model.id == row_id)
        result = await db.execute(query)

        if data := result.scalar_one_or_none():
            logger.debug(f"Found {self.model.__name__} with ID: {row_id}")
            return data

        error_msg = f"{self.model.__name__} with ID: {row_id} not found."
        logger.error(error_msg)
        raise ElementNotFoundError(error_msg)

    async def get_one_by_field(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        field: str,
        value: str,
    ) -> ModelType:
        """Returns an object of the model specified.

        Args:
            db (Session): Database session.
            field (str): Field of the row in the DB.
            value (str): Value to compare the Field with.

        Returns:
            ModelType: Element.

        Raises:
            ElementNotFoundError: If the element is not found.
        """
        logger.debug(f"Getting {self.model.__name__} with {field}: {value}")
        column: InstrumentedAttribute = getattr(self.model, field)
        query = select(self.model).where(column == value)
        result = await db.execute(query)

        if data := result.scalar_one_or_none():
            logger.debug(f"Found {self.model.__name__} with {field}: {value}")
            return data

        error_msg = f"{self.model.__name__} with {field}: {value} not found."
        logger.error(error_msg)
        raise ElementNotFoundError(error_msg)

    async def get_one_by_fields(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        filters: list[Filter],
    ) -> ModelType:
        """Returns an object of the model specified.

        Args:
            db (Session): Database session.
            filters (dict[str, Tuple[str, object]]): Filters to apply, where each filter
                is a tuple of (operator, value).

        Returns:
            ModelType: Element.

        Raises:
            ElementNotFoundError: If the element is not found.
        """
        logger.debug(f"Getting {self.model.__name__} with filters: {filters}")
        filter_clauses = self._get_filters(filters)

        query = select(self.model).where(*filter_clauses)
        result = await db.execute(query)

        if data := result.scalar_one_or_none():
            logger.debug(f"Found {self.model.__name__} with filters: {filters}")
            return data
        error_msg = f"{self.model.__name__} with filters: {filters} not found."
        logger.error(error_msg)
        raise ElementNotFoundError(error_msg)

    async def get_list(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        offset: int | None = None,
        limit: int | None = None,
        filters: list[Filter] | None = None,
        filter_is_logic_and: bool = True,
        order_by: str = "dummy_id",
        order_direction: Literal["asc", "desc"] = "asc",
        join_fields: list[str] | None = None,
    ) -> Sequence[ModelType | None]:
        """Get a list of elements that can be filtered.

        Result requires mapping the objects to the desired response.

        Args:
            db (Session): Database session.
            offset (int | None = None): Omit a specified number of rows before
                the beginning of the result set. Defaults to None.
            limit (int | None = None): Limit the number of rows returned from a query.
                Defaults to None.
            filters (list[Filter] | None): Filters to apply. Defaults to None. Each filter is an
                instance of :class:`Filter` with the following fields:

                - field: str → name of the models`s column for (example "email").
                - operator: str → one of "eq", "neq", "contains", "gt", "gte", "lt", "lte".
                - value: Any → value to comparison.

                example:
                ```python
                filters = [
                    Filter(field="name", operator="contains", value="John"),
                    Filter(field="age", operator="gte", value=18),
                ]
            filter_is_logic_and (bool, optional): If True, the filters are applied with AND logic,
                otherwise with OR logic. Defaults to True.
            order_by (str, optional): Field to order the results by. Defaults to "dummy_id".
            order_direction (Literal["asc", "desc"], optional): Order direction for the results.
            join_fields (list[str], optional): List of foreign key fields to perform
                joined loading on. Defaults to None.
                E.g. ["profile", "address"].

        Returns:
            list[ModelType | None]: Result with the Data.
        """
        logger.debug(f"Getting list of {self.model.__name__}")
        query = select(self.model)

        if join_fields:
            for join_field in join_fields:
                query = query.join(getattr(self.model, join_field))

        if filters:
            filter_clauses = self._get_filters(filters)
            if filter_is_logic_and:
                query = query.where(*filter_clauses)
            else:
                query = query.filter(or_(*filter_clauses))
            logger.debug(f"Filters applied: {filters}")

        # Order by ID to ensure consistent ordering
        if order_direction == "desc":
            query = query.order_by(getattr(self.model, order_by).desc())
        else:
            query = query.order_by(getattr(self.model, order_by))
        logger.debug(f"Order by: {order_by}")

        # Apply offset and limit - Pagination
        if offset:
            query = query.offset(offset)
            logger.debug(f"Offset: {offset}")
        if limit:
            query = query.limit(limit)
            logger.debug(f"Limit: {limit}")

        string_query = str(query)
        logger.debug(f"Query: {string_query}")
        result = await db.execute(query)

        if data := result.scalars().all():
            logger.debug(f"Found list of {self.model.__name__}")
            return data

        logger.error(f"List of {self.model.__name__} not found")
        return []

    async def count(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        filters: list[Filter] | None = None,
    ) -> int:
        """Get the number of elements that can be filtered.

        Args:
            db (Session): Database session.
            filters (list[Filter] | None): Filters to apply. Defaults to None. Each filter is an
                instance of :class:`Filter` with the following fields:

                - field: str → name of the models`s column for (example "email").
                - operator: str → one of "eq", "neq", "contains", "gt", "gte", "lt", "lte".
                - value: Any → value to comparison.

                example:
                ```python
                filters = [
                    Filter(field="name", operator="contains", value="John"),
                    Filter(field="age", operator="gte", value=18),
                ]

        Returns:
            int: Number of elements that match the query.
        """
        logger.debug(f"Counting {self.model.__name__}")
        count_query = select(func.count()).select_from(self.model)

        if filters:
            filter_clauses = self._get_filters(filters)
            count_query = count_query.where(*filter_clauses)
            logger.debug(f"Filters applied: {filters}")

        result = await db.execute(count_query)

        if data := result.scalar():
            logger.debug(f"Counted {self.model.__name__}: {data}")
            return data

        logger.error(f"Count of {self.model.__name__} not found")
        return 0

    async def create(self: "DAOBase[ModelType]", db: AsyncSession, data: ModelType) -> ModelType:
        """Creates a new record in the database.

        Args:
            db (Session): The database session.
            data (ModelType): The data to be created.

        Returns:
            ModelType: The created data.

        Raises:
            OperationalError: If an error occurs during the operation.
        """
        logger.debug(f"Creating {self.model.__name__} object {data}")
        try:
            db.add(data)
            await db.commit()
            await db.refresh(data)
            logger.debug(f"Created {self.model.__name__} object {data}")

        except OperationalError:
            await db.rollback()
            logger.exception(f"Failed to create {self.model.__name__} object {data}")
            raise
        else:
            return data

    async def update(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        data: ModelType,
    ) -> ModelType:
        """Update an existing record in the database.

        This method merges the provided data with the existing record in the database.
        If the operation is successful, the updated record is returned.
        If an OperationalError occurs during the operation, the changes are rolled back.

        Args:
            db (Session): The database session.
            data (ModelType): The data to be updated.

        Returns:
            ModelType: The updated record.

        Raises:
            OperationalError: If an error occurs during the operation.
        """
        logger.debug(f"Updating {self.model.__name__} with object {data}")
        try:
            merged = await db.merge(data)
            await db.commit()
            await db.refresh(merged)
            logger.debug(f"Updated {self.model.__name__} with object {data}")

        except OperationalError:
            await db.rollback()
            logger.exception(f"Failed to update {self.model.__name__} object {data}")
            raise
        else:
            return merged

    async def delete_row(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        model_obj: ModelType,
    ) -> bool:
        """Delete a record from the database.

        This method retrieves the record and deletes it from the database.
        If the operation is successful, True is returned.
        If an OperationalError occurs during the operation, the changes are rolled back.

        Args:
            db (AsyncSession): The database session.
            model_obj (ModelType): The object of the record to be deleted.

        Returns:
            bool: True if the object was deleted, otherwise raises an error.

        Raises:
            OperationalError: If an error occurs during the operation.
        """
        logger.debug(f"Deleting {self.model.__name__} object {model_obj}")
        try:
            await db.delete(model_obj)
            await db.commit()
            logger.debug(f"Deleted {self.model.__name__} object {model_obj}")

        except OperationalError:
            await db.rollback()
            logger.exception(f"Failed to delete {self.model.__name__} object {model_obj}")
            raise
        else:
            return True

    async def soft_delete_row(
        self: "DAOBase[ModelType]",
        db: AsyncSession,
        model_obj: ModelType,
    ) -> ModelType:
        """Soft delete a record from the database.

        This method retrieves the record and sets its 'deleted_on' attribute to the
        current time.
        If the operation is successful, the updated record is returned.
        If an OperationalError occurs during the operation, the changes are rolled back.
        If the model does not support soft delete, a ValueError is raised.

        Args:
            db (Session): The database session.
            model_obj (ModelTypedelType): The object of the record to be soft deleted.

        Returns:
            ModelType: The updated record if found and soft deleted.

        Raises:
            OperationalError: If an error occurs during the operation.
            ValueError: If the model does not support soft delete.
        """
        logger.debug(f"Soft deleting {self.model.__name__} object {model_obj}")
        try:
            if not hasattr(model_obj, "deleted_on") or not hasattr(model_obj, "soft_delete"):
                logger.error("Model does not support soft delete.")
                error_message = "Model does not support soft delete."
                raise ValueError(error_message)

            logger.debug(f"Soft deleting {self.model.__name__} by updating its values")

        except OperationalError:
            await db.rollback()
            logger.exception(f"Failed to soft delete {self.model.__name__} {model_obj}")
            raise
        else:
            return await self.update(db, model_obj.soft_delete())
