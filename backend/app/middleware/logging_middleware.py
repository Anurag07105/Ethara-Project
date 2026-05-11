"""
Request logging middleware.
Logs incoming requests and response times for monitoring.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ethara.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all incoming HTTP requests with timing information."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Log the incoming request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"[Client: {request.client.host if request.client else 'unknown'}]"
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log the response
            logger.info(
                f"← {request.method} {request.url.path} "
                f"[Status: {response.status_code}] "
                f"[Duration: {duration:.3f}s]"
            )

            # Add timing header
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"[Error: {str(e)}] "
                f"[Duration: {duration:.3f}s]"
            )
            raise
