"""Reusable error response schema definitions for API routes."""

from app.controller.api.v1.errors.schema import ErrorMessage

#: Common HTTP error responses mapped to their OpenAPI schema representation.
CommonBadResponses = {
    400: {"model": ErrorMessage, "description": "Bad Request."},
    401: {"model": ErrorMessage, "description": "Unauthorized."},
    403: {"model": ErrorMessage, "description": "Forbidden."},
    404: {"model": ErrorMessage, "description": "Not Found."},
    409: {"model": ErrorMessage, "description": "Conflict."},
    422: {"model": ErrorMessage, "description": "Unprocessable Entity."},
    500: {"model": ErrorMessage, "description": "Internal Server Error."},
    501: {"model": ErrorMessage, "description": "Not Implemented."},
    502: {"model": ErrorMessage, "description": "Bad Gateway."},
    503: {"model": ErrorMessage, "description": "Service Unavailable."},
    504: {"model": ErrorMessage, "description": "Gateway Timeout."},
}


def compose_responses(success_responses: dict) -> dict:
    """
    Compose a dictionary of success and standardized error responses.

    Example:
        compose_responses({
            200: {"model": DummyListResponse, "description": "OK."},

            201: {"model": DummyCreatedResponse, "description": "Created."},

            204: {"model": None, "description": "No Content."},
        })

    Args:
        success_responses (dict): Response models for successful status codes (e.g., 200, 201).

    Returns:
        dict: Merged mapping of success and standard error response schemas.
    """
    return {**success_responses, **CommonBadResponses}
