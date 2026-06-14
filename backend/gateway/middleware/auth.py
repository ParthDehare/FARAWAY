import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

DEMO_MODE = os.getenv("RAILNERV_DEMO", "true").lower() == "true"
API_KEY = os.getenv("RAILNERV_API_KEY", "railnerv-sentinel-key")

EXEMPT_PATHS = {"/api/health", "/docs", "/redoc", "/openapi.json", "/ws/socket.io"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if DEMO_MODE:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        key = request.headers.get("X-API-Key")
        if not key or key != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key. Set X-API-Key header."},
            )

        return await call_next(request)
