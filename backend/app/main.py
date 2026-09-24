import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.logging_setup import setup_logging
from app.errors import (
    AppError,
    app_error_handler,
    validation_error_handler,
    starlette_http_exception_handler,
    generic_exception_handler,
)
from app.routers import health, pages, ai

# Initialize logging
setup_logging()
logger = logging.getLogger("bpe.app")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Bangla Page Explainer API",
        version="0.1.0",
        description="Backend API for Bangla Page Explainer Chrome Extension"
    )

    # CORS configuration
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    origins.extend(settings.cors_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request timing & structured logging middleware
    @app.middleware("http")
    async def timing_and_logging_middleware(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Response-Time"] = f"{latency_ms:.1f}ms"
        
        # Log HTTP request info (never log query params or bodies)
        logger.info(
            f"{request.method} {request.url.path} status={response.status_code} latency={latency_ms:.1f}ms"
        )
        return response

    # Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include Routers
    app.include_router(health.router)
    app.include_router(pages.router)
    app.include_router(ai.router)

    return app


app = create_app()
