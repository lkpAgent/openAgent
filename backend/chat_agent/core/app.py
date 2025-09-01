"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings
from .logging import setup_logging
from ..api.routes import router
from ..db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logging.info("Starting up ChatAgent application...")
    await init_db()
    logging.info("Database initialized")
    
    yield
    
    # Shutdown
    logging.info("Shutting down ChatAgent application...")


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if settings is None:
        from .config import get_settings
        settings = get_settings()
    
    # Setup logging
    setup_logging(settings.logging)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A modern chat agent application with Vue frontend and FastAPI backend",
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Add middleware
    setup_middleware(app, settings)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(router, prefix="/api")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": "Chat Agent API is running"}
    
    # Test endpoint
    @app.get("/test")
    async def test_endpoint():
        return {"message": "API is working"}
    
    return app


def setup_middleware(app: FastAPI, settings: Settings) -> None:
    """Setup application middleware."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.cors.allowed_methods,
        allow_headers=settings.cors.allowed_headers,
    )
    
    # Trusted host middleware (for production)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure this properly in production
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers."""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail,
                    "status_code": exc.status_code
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logging.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "Internal server error"
                }
            }
        )


# Create the app instance
app = create_app()