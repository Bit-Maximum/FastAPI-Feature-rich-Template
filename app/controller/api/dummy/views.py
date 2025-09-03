from typing import Annotated

from fastapi import APIRouter
from fastapi.param_functions import Depends

from app.controller.api.dummy.schema import DummyModelDTO, DummyModelInputDTO
from app.db.dao.dummy_dao import DummyDAO
from app.db.models.dummy_model import DummyModel

router = APIRouter()


@router.get("/", response_model=list[DummyModelDTO])
async def get_dummy_models(
    dummy_dao: Annotated[DummyDAO, Depends()],
    limit: int = 10,
    offset: int = 0,
) -> list[DummyModel]:
    """
    Retrieve all dummy objects from the database.

    :param limit: limit of dummy objects, defaults to 10.
    :param offset: offset of dummy objects, defaults to 0.
    :param dummy_dao: DAO for dummy models.
    :return: list of dummy objects from database.
    """
    return await dummy_dao.get_all_dummies(limit=limit, offset=offset)


@router.put("/")
async def create_dummy_model(
    new_dummy_object: DummyModelInputDTO,
    dummy_dao: Annotated[DummyDAO, Depends()],
) -> None:
    """
    Creates dummy model in the database.

    :param new_dummy_object: new dummy model item.
    :param dummy_dao: DAO for dummy models.
    """
    await dummy_dao.create_dummy_model(name=new_dummy_object.name)
