"""
Financial Intelligence Platform — FastAPI Application

Main entry point for the backend API.
Architecture principle: The AI agent has NO direct database access.
It can only call tools. The tools are API endpoints. This makes
the system auditable and controllable.
"""

import time
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.utils.logging import get_logger, set_trace_id, set_user_id, setup_logging

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # --- Startup ---
    setup_logging(
        level=settings.log_level,
        service_name="api",
        json_output=settings.is_production,
    )
    log.info(
        "Starting Financial Intelligence Platform",
        env=settings.app_env,
        debug=settings.app_debug,
    )

    # Initialize database
    await init_db()

    # Initialize Sentry for error tracking (if configured)
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            traces_sample_rate=0.1,
        )
        log.info("Sentry initialized")

    yield

    # --- Shutdown ---
    await close_db()
    log.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Financial Intelligence Platform",
        description=(
            "Evidence-backed financial intelligence API. "
            "Every answer is verifiable, every claim is cited, "
            "every source is tracked."
        ),
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Request tracing middleware ---
    @app.middleware("http")
    async def tracing_middleware(request: Request, call_next) -> Response:
        """Attach trace_id to every request and log request/response."""
        # Get or generate trace ID
        trace_id = request.headers.get("X-Trace-ID")
        trace_id = set_trace_id(trace_id)

        # Set user ID if authenticated (placeholder for auth integration)
        set_user_id(None)

        start_time = time.perf_counter()

        log.info(
            "Request started",
            method=request.method,
            path=str(request.url.path),
            trace_id=trace_id,
        )

        response = await call_next(request)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        log.info(
            "Request completed",
            method=request.method,
            path=str(request.url.path),
            status=response.status_code,
            duration_ms=duration_ms,
            trace_id=trace_id,
        )

        # Propagate trace ID in response header
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time-MS"] = str(duration_ms)

        return response

    # --- Health check ---
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        System health check.

        Returns basic system status. Used by monitoring and load balancers.
        """
        return {
            "status": "healthy",
            "service": settings.app_name,
            "environment": settings.app_env,
            "version": "0.1.0",
        }

    @app.get("/health/detailed", tags=["System"])
    async def detailed_health_check():
        """
        Detailed health check including database and cache status.

        This endpoint is for internal monitoring only.
        """
        db_status = "unknown"
        try:
            from sqlalchemy import text
            from app.database import get_engine
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        redis_status = "unknown"
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            redis_status = "healthy"
            await r.aclose()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"

        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "service": settings.app_name,
            "environment": settings.app_env,
            "version": "0.1.0",
            "components": {
                "database": db_status,
                "cache": redis_status,
            },
        }

    # --- Register API routers ---
    # These will be added as we build each phase
    # from app.api.companies import router as companies_router
    # app.include_router(companies_router, prefix="/api/v1")

    return app


# Application instance
app = create_app()
