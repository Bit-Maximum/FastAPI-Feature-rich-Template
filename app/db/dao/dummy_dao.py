from app.db.dao.base import DAOBase
from app.db.models.dummy_model import DummyModel


class DummyDAO(DAOBase[DummyModel]):
    """CRUD operations for the Dummy model."""


dummy_dao = DummyDAO(DummyModel)
