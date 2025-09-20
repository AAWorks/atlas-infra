"""
Global Middleware
"""

import time
import logging
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class GlobalMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logging.info(f"➡️ Request: {request.method} {request.url}")

        try:
            response: Response = await call_next(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception:
            logging.exception("Unhandled error")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        logging.info(
            f"⬅️ Response status: {response.status_code} ({process_time:.3f}s)"
        )

        return response
