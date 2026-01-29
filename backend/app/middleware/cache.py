"""
Caching middleware for API responses
"""

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add cache headers for GET requests.
    """

    def __init__(self, app, cache_time: int = 300):
        super().__init__(app)
        self.cache_time = cache_time

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add cache headers for GET requests to reference data
        if request.method == "GET":
            # Cache reference data for 1 hour
            if "/reference/" in str(request.url.path):
                response.headers["Cache-Control"] = f"public, max-age=3600"
            # Cache static uploads forever (immutable)
            elif "/uploads/" in str(request.url.path):
                response.headers["Cache-Control"] = (
                    "public, max-age=31536000, immutable"
                )
            # No cache for other API endpoints (default)
            elif "/api/" in str(request.url.path):
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )

        return response
