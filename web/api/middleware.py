"""Request logging, request-id correlation, and rate limiting."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .observability import REQUEST_COUNT, REQUEST_LATENCY


def configure_logging() -> structlog.stdlib.BoundLogger:
    """Idempotent structlog setup — JSON logs to stdout."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger("aura.web")


logger = configure_logging()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a request id, log timing, and emit Prometheus counters."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("x-request-id") or "rq_" + uuid.uuid4().hex[:12]
        structlog.contextvars.bind_contextvars(request_id=rid, path=request.url.path)
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            elapsed = time.perf_counter() - start
            route = request.scope.get("route")
            route_name = getattr(route, "path", request.url.path)
            try:
                REQUEST_LATENCY.labels(
                    method=request.method, route=route_name, status=str(status_code)
                ).observe(elapsed)
                REQUEST_COUNT.labels(
                    method=request.method, route=route_name, status=str(status_code)
                ).inc()
            except Exception:  # pragma: no cover - metrics must never break a request
                pass
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=status_code,
                latency_ms=round(elapsed * 1000, 2),
            )
            structlog.contextvars.clear_contextvars()


# Shared limiter — used by main.py via @limiter.limit("...") decorators.
limiter = Limiter(key_func=get_remote_address, default_limits=["240/minute"])


def install_middleware(app: FastAPI) -> None:
    """Wire all middleware + the rate limiter onto a FastAPI app."""
    from slowapi.middleware import SlowAPIMiddleware

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestIDMiddleware)


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": "rate limit exceeded", "limit": str(exc.detail)},
        headers={"Retry-After": "60"},
    )
