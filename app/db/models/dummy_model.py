from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String

from app.db.models.base import Base


class DummyModel(Base):
    """Model for demo purpose."""

    name: Mapped[str] = mapped_column(String(length=200), nullable=False)
