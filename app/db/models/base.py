"""SQL Alchemy models declaration.

https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html#example-two-dataclasses-with-declarative-table
Dataclass style for powerful autocompletion support.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.db.meta import meta


class BaseMetadata(DeclarativeBase):
    """BaseMetadata for all models."""

    # see: https://alembic.sqlalchemy.org/en/latest/naming.html#integration-of-naming-conventions-into-operations-autogenerate
    metadata = meta


class Base(BaseMetadata):
    """Abstract base class for models with UUID.

    This class provides a 'dummy_id' attribute for models, which is a UUID that is automatically
    generated when a record is created. It also provides a '__tablename__' attribute,
    which is automatically generated from the class name.

    Attributes:
        id (Mapped[UUID]): The unique identifier of the record. This is set automatically
            when the record is first saved to the database.

    Methods:
        __tablename__(): Returns the table name, which is the lowercased class name.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )

    # Generate __tablename__ automatically
    @declared_attr
    @classmethod
    def __tablename__(cls: type["BaseMetadata"]) -> str:
        """Generate the table name automatically from the class name.

        This method returns the lowercased class name as the table name.

        Returns:
            str: The table name.
        """
        return cls.__name__.lower()


class BaseTimestamps(Base):
    """Abstract base class for models with creation and modification timestamps.

    This class provides 'created' and 'modified' attributes for models,
    which automatically track the time when a record is created and the last time it was modified.

    Attributes:
        created (Mapped[datetime]): The time when the record was created. This is set automatically
            when the record is first saved to the database.
        modified (Mapped[datetime]): The last time the record was modified. This is updated
            automatically every time the record is saved to the database.

    """

    __abstract__ = True
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseDeletedOn(Base):
    """Abstract base class for models supporting soft delete.

    This class provides a 'deleted_on' attribute for models, which is used to mark a record
    as deleted without actually removing it from the database.
    The 'deleted_on' attribute is set to the current time when the 'soft_delete' method is called.

    Attributes:
        deleted_on (Mapped[datetime]): The time when the record was marked as deleted.
            If this is None, the record is not considered deleted.

    Methods:
        soft_delete(): Marks the record as deleted by setting 'deleted_on' to the current time.
    """

    __abstract__ = True
    deleted_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
    )

    def soft_delete(self: "BaseDeletedOn") -> "BaseDeletedOn":
        """Soft delete the current record.

        This method sets the 'deleted_on' attribute of the current record to the current time.
        The record is not removed from the database, but is marked as deleted.

        Returns:
            self: The updated record.
        """
        self.deleted_on = datetime.now(UTC)
        return self
