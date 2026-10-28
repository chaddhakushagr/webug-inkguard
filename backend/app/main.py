import os
import uuid
import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.api.routers import (
    auth as auth_router,
    users as users_router,
    kb as kb_router,
    submissions as submissions_router,
    findings as findings_router,
    comments as comments_router,
    insights as insights_router,
    audit as audit_router,
    settings as settings_router,
    evaluation as evaluation_router,
)


from contextlib import asynccontextmanager
from app.adapters.db.session import wait_for_db, run_migrations_and_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Free databases (e.g. Neon) suspend on idle; connect with retry
    wait_for_db()
    # Apply Alembic migrations to head and seed if empty
    run_migrations_and_seed()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="Inkguard Brand Governance API",
        version="0.2.0",
        description="Automated pre-publication brand governance platform for marketing copy and claims verification.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Request ID and Timing Middleware
    @app.middleware("http")
    async def request_id_and_timing_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id
        start_time = time.time()

        # Security hardening: Gate /dev and /dev/ui routes in production
        if settings.APP_ENV.lower() == "production" and request.url.path.startswith("/dev"):
            return JSONResponse(
                status_code=404,
                content={
                    "code": "HTTP_404",
                    "message": f"Endpoint '{request.url.path}' not found",
                    "details": {"path": request.url.path, "request_id": req_id},
                },
                headers={"X-Request-ID": req_id},
            )

        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"

        # Intercept 404 on /api/ routes to guarantee consistent JSON error envelope
        if request.url.path.startswith("/api/") and response.status_code == 404:
            if not response.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    status_code=404,
                    content={
                        "code": "HTTP_404",
                        "message": f"Endpoint '{request.url.path}' not found",
                        "details": {"path": request.url.path, "request_id": req_id},
                    },
                    headers={"X-Request-ID": req_id},
                )
        return response

    # Global Consistent Error Envelope Handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {"path": request.url.path, "request_id": req_id},
            },
            headers={"X-Request-ID": req_id or ""},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload structure.",
                "details": {
                    "errors": exc.errors(),
                    "request_id": req_id,
                },
            },
            headers={"X-Request-ID": req_id or ""},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred processing the request.",
                "details": {"error": str(exc), "request_id": req_id},
            },
            headers={"X-Request-ID": req_id or ""},
        )

    # Include all API v1 routers with prefix
    app.include_router(auth_router.router, prefix="/api/v1")
    app.include_router(users_router.router, prefix="/api/v1")
    app.include_router(kb_router.router, prefix="/api/v1")
    app.include_router(submissions_router.router, prefix="/api/v1")
    app.include_router(findings_router.router, prefix="/api/v1")
    app.include_router(comments_router.router, prefix="/api/v1")
    app.include_router(insights_router.router, prefix="/api/v1")
    app.include_router(audit_router.router, prefix="/api/v1")
    app.include_router(settings_router.router, prefix="/api/v1")
    app.include_router(evaluation_router.router, prefix="/api/v1")

    # Frontend Static Files (if exported build is present)
    static_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "static")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/out")),
    ]
    for static_dir in static_dirs:
        if os.path.exists(static_dir) and os.path.isdir(static_dir):
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
            break

    return app


app = create_app()
