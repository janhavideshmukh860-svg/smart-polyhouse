"""
Smart Polyhouse Backend - FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.database.database import check_database_connection

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-Driven Intelligent Polyhouse Monitoring, Prediction, Disease Detection, "
        "Irrigation Optimization and Decision Support System - Part 1 Backend API."
    ),
    # NOTE: intentionally always False, regardless of settings.APP_DEBUG.
    # Starlette's debug mode renders raw Python tracebacks directly to the
    # HTTP response for unhandled exceptions, BEFORE our custom
    # `unhandled_exception_handler` below gets a chance to run - which
    # would violate the "never return raw Python exceptions" API design
    # requirement. settings.APP_DEBUG still controls log verbosity via
    # LOG_LEVEL; use server logs (not HTTP responses) for debugging.
    debug=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Centralized exception handling - never leak raw Python tracebacks/exceptions
# to API clients (per API design requirements for Lovable consumption).
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": str(exc.detail)}},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "422",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "500", "message": "An internal server error occurred."}},
    )


@app.on_event("startup")
async def on_startup():
    logger.info("Starting %s (env=%s, version=%s)", settings.APP_NAME, settings.APP_ENV, settings.APP_VERSION)
    db_ok = check_database_connection()
    if db_ok:
        logger.info("Database connection: OK")
    else:
        if settings.ALLOW_START_WITHOUT_DB:
            logger.warning(
                "Database connection FAILED - starting anyway because ALLOW_START_WITHOUT_DB=true. "
                "DB-dependent endpoints will return 503 until DATABASE_URL is correctly configured."
            )
        else:
            logger.error("Database connection FAILED and ALLOW_START_WITHOUT_DB=false - refusing to start.")
            raise RuntimeError("Database connection failed at startup. Set ALLOW_START_WITHOUT_DB=true to bypass.")

    from app.ml.disease.inference import disease_inference_service
    from app.ml.irrigation.inference import calibration_service, forecasting_service

    logger.info("Disease model available: %s", disease_inference_service.is_available())
    logger.info("Irrigation calibration model available: %s", calibration_service.is_available())
    logger.info("Irrigation forecasting models available: %s", forecasting_service.is_available())


@app.get("/", tags=["System"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }
