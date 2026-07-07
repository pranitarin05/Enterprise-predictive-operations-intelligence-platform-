"""
Health check route.

Deliberately thin: it only calls the service and shapes the HTTP response.
No business logic lives here — that's the whole point of the layering.
"""

from fastapi import APIRouter, Response, status

from app.services.health_service import get_health_status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check(response: Response):
    result = get_health_status()

    if result["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result
