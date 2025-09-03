"""Defines data models for representing hyperlinks and pagination configuration."""

import math

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

EXAMPLE_URL = "http://localhost:8000/api/v1/dummies?limit=10&offset=0"


def calculate_page_number(offset: int, limit: int) -> int:
    """Calculate the page number based on the given offset and limit.

    Args:
        offset (int): The starting index of the current page (0-based).
        limit (int): The maximum number of elements per page.

    Raises:
        ValueError: If the limit is not a positive integer, or if the
            total elements is not a non-negative integer.

    Returns:
        int: The page number (1-based).
    """
    if limit <= 0:
        error_message = "Limit must be a positive integer."
        raise ValueError(error_message)

    if offset < 0:
        error_message = "Offset must be a non-negative integer."
        raise ValueError(error_message)

    return math.ceil((offset + 1) / limit)


def calculate_total_pages(limit: int, total_elements: int) -> int:
    """Compute the total number of pages based on limit and total elements.

    Args:
        limit (int): The maximum number of elements per page.
        total_elements (int): The total number of elements.

    Raises:
        ValueError: If limit is not positive or total_elements is negative.

    Returns:
        int: Total number of pages required.
    """
    if limit <= 0:
        error_message = "Limit must be a positive integer."
        raise ValueError(error_message)

    if total_elements < 0:
        error_message = "Total elements must be a non-negative integer."
        raise ValueError(error_message)

    return math.ceil(total_elements / limit)


class HyperLink(BaseModel):
    """Represents a hyperlinked reference.

    Attributes:
        href (str, optional): The URL reference. Defaults to None.
    """

    href: str | None = Field(
        default=None,
        examples=[EXAMPLE_URL],
    )


class PaginationLinks(BaseModel):
    """Represents a set of hyperlinks for pagination purposes.

    Attributes:
        first (HyperLink, optional): The link to the first page. Defaults to None.
        prev (HyperLink, optional): The link to the previous page. Defaults to None.
        actual (HyperLink): The link to the current page.
        next (HyperLink, optional): The link to the next page. Defaults to None.
        last (HyperLink, optional): The link to the last page. Defaults to None.
    """

    first: HyperLink | None = Field(
        default=None,
        examples=[{"href": EXAMPLE_URL}],
    )
    prev: HyperLink | None = Field(
        default=None,
        examples=[{"href": EXAMPLE_URL}],
    )
    actual: HyperLink = Field(
        examples=[{"href": EXAMPLE_URL}],
    )
    next: HyperLink | None = Field(
        default=None,
        examples=[{"href": EXAMPLE_URL}],
    )
    last: HyperLink | None = Field(
        default=None,
        examples=[{"href": EXAMPLE_URL}],
    )

    @classmethod
    def generate_pagination_links(
        cls: type["PaginationLinks"],
        url: str,
        total_pages: int,
        limit: int,
        offset: int,
        total_elements: int,
    ) -> "PaginationLinks":
        """Generate pagination links and return a new instance of PaginationLinks.

        Args:
            url (str): The base URL for the pagination links.
            total_pages (int): The total number of pages available.
            limit (int): The number of elements per page.
            offset (int): The current offset for the pagination.
            total_elements (int): The total number of elements.

        Returns:
            PaginationLinks: An object containing HyperLink instances for
                first, actual, prev, next, and last pages.
                The actual page link is based on the provided offset.
        """
        base_href = f"{url}&" if "?" in url else f"{url}?"
        base_href = f"{base_href}limit={limit}"
        self_href = f"{base_href}&offset={offset}"
        actual = HyperLink(href=str(AnyHttpUrl(self_href)))

        if total_elements == 0:
            return cls(first=None, prev=None, actual=actual, next=None, last=None)

        last_page = total_pages - 1

        first_href = f"{base_href}&offset=0"
        prev_href = f"{base_href}&offset={max(0, offset - limit)}"
        next_href = f"{base_href}&offset={min(last_page * limit, offset + limit)}"
        last_href = f"{base_href}&offset={max(0, (last_page - 1) * limit)}"

        first_page = HyperLink(href=str(AnyHttpUrl(first_href)))
        prev_page = (
            HyperLink(href=str(AnyHttpUrl(prev_href)))
            if offset > 0
            else HyperLink(href=str(AnyHttpUrl(self_href)))
        )
        next_page = (
            HyperLink(href=str(AnyHttpUrl(next_href)))
            if offset < last_page * limit
            else HyperLink(href=str(AnyHttpUrl(self_href)))
        )
        last_page = HyperLink(href=str(AnyHttpUrl(last_href)))

        return cls(first=first_page, prev=prev_page, actual=actual, next=next_page, last=last_page)


class Pagination(BaseModel):
    """Represents a pagination configuration for handling offsets,
    limits, page numbers, total pages, total elements, and pagination links.

    Attributes:
    - offset (int | None): The offset for pagination.
    - limit (int | None): The limit of elements per page.
    - page_number (int | None): The current page number.
    - total_pages (int | None): The total number of pages.
    - total_elements (int | None): The total number of elements.
    - links (PaginationLinks | None): Links associated with the pagination.

    Class Methods:
    - offset_validator(cls: type[Pagination], value: int | None) -> int | None:
        Validates the offset value based on specified constraints.

    Note: The offset value must be within the range [0, 255].
    """

    offset: int | None = Field(default=None)
    limit: int | None = Field(default=None)
    page_number: int | None = Field(default=None)
    total_pages: int | None = Field(default=None)
    total_elements: int | None = Field(default=None)
    links: PaginationLinks | None = Field(
        default=None,
        examples=[
            {
                "actual": {"href": EXAMPLE_URL},
                "first": {"href": EXAMPLE_URL},
                "prev": {"href": EXAMPLE_URL},
                "next": {"href": EXAMPLE_URL},
                "last": {"href": EXAMPLE_URL},
            },
        ],
    )

    @field_validator(
        "offset", "limit", "page_number", "total_pages", "total_elements", mode="before"
    )
    def validate_values(cls: type["Pagination"], value: int | None) -> int | None:
        """Validates values of the model."""
        max_value = 1000
        min_value = 0
        if value and (value > max_value or value < min_value):
            error_message = f"Must be less than {min_value} or more than {max_value}."
            raise ValueError(error_message)
        return value

    @classmethod
    def get_pagination(
        cls: type["Pagination"],
        offset: int,
        limit: int,
        total_elements: int,
        url: str,
    ) -> "Pagination":
        """Generate pagination information based on the provided parameters.

        Parameters:
        - offset (int): The starting index of the current page.
        - limit (int): The maximum number of elements per page.
        - no_elements (int): The total number of elements to be paginated.
        - url (str): The base URL used for generating pagination links.

        Returns:
        Pagination: An object containing pagination information, including offset,
        limit, current page number, total pages, total elements, and pagination links.
        """
        total_pages = calculate_total_pages(limit, total_elements)
        links = PaginationLinks.generate_pagination_links(
            url=url,
            total_pages=total_pages,
            limit=limit,
            offset=offset,
            total_elements=total_elements,
        )
        return cls(
            offset=offset,
            limit=limit,
            page_number=calculate_page_number(offset, limit),
            total_pages=total_pages,
            total_elements=total_elements,
            links=links,
        )


HyperLink.model_rebuild()
PaginationLinks.model_rebuild()
Pagination.model_rebuild()
