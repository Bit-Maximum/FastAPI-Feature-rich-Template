from app.controller.api.v1.dummy.schema import DummyCreate, DummyDataResponse
from app.db.models.dummy_model import DummyModel


def to_response(model: DummyModel) -> DummyDataResponse:
    """
    Convert a DummyModel instance to a DummyDetailResponse.

    Args:
        model (DummyModel): The database model instance.

    Returns:
        DummyDetailResponse: The API response schema.
    """
    return DummyDataResponse(
        dummyId=str(model.id),
        name=model.name,
    )


def to_model(dto: DummyCreate) -> DummyModel:
    """
    Convert a DummyCreate DTO to a DummyModel instance.

    Args:
        dto (DummyCreate): The data transfer object with input data.

    Returns:
        DummyModel: The new database model instance.
    """
    return DummyModel(name=dto.name)
