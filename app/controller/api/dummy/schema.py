from pydantic import BaseModel, ConfigDict, Field

from app.controller.utils.pagination import Pagination


class DummyModelDTO(BaseModel):
    """
    DTO for dummy models.

    It returned when accessing dummy models from the API.
    """

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DummyModelInputDTO(BaseModel):
    """DTO for creating new dummy model."""

    name: str


class DummyDataResponse(BaseModel):
    """Model for the data returned by a Dummy API endpoint."""

    dummyId: str = Field(..., examples=["a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"])
    name: str = Field(..., examples=["John Doe"])


class DummyCreate(BaseModel):
    """Model for creating a new dummy model."""

    name: str = Field(..., examples=["John Doe"])


class DummyUpdate(BaseModel):
    """Model for updating a Dummy."""

    name: str | None = Field(default=None, examples=["John Doe"])


class CustomerListResponse(BaseModel):
    """Model for the response of a dummy API endpoint.

    This class represents the structure of the response returned by an customer API endpoint.
    It includes a 'data' attribute, which is a list of `CustomerListData` objects,
    and a 'pagination' attribute, which is a `Pagination` object.

    Attributes:
        data (list[CustomerListData] | None): The data returned by the endpoint.
            This is a list of `CustomerListData` objects. If no data is returned,
            this is None.
        pagination (Pagination | None): The pagination information for the data.
            If no pagination information is provided, this is None.
    """

    data: list[DummyDataResponse] = Field(default=[])
    pagination: Pagination | None = Field(default=None)
