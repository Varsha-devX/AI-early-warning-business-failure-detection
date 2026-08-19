"""
FastAPI Application Entry Point
================================
EarlySight AI — AI Early Warning Business Failure Detection

Sets up the FastAPI application with:
- CORS middleware
- Logging configuration
- Router registration
- Database initialization
- Swagger documentation
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.database.connection import init_db


# Configure Loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events: startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("AI Early Warning Business Failure Detection")
    logger.info("=" * 60)

    settings = get_settings()
    settings.ensure_directories()

    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Database: {settings.database_url[:50]}...")
    logger.info(f"Gemini Model: {settings.gemini_model}")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Pre-train ML model if not exists
    import os
    if not os.path.exists(settings.model_path):
        logger.info("Training ML model (first run)...")
        from app.ml_models.train_model import train_model
        metrics = train_model(output_dir=settings.trained_models_dir)
        logger.info(f"Model trained: {metrics}")

    logger.info("Application startup complete")
    yield

    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="EarlySight AI — AI Early Warning Business Failure Detection",
        description=(
            "EarlySight AI: AI-powered platform for detecting early warning signs of financial distress. "
            "Analyzes financial statements and business news using XGBoost, SHAP, FinBERT, "
            "and Gemini AI to generate actionable business intelligence."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "https://ai-early-warning-business-fail-git-7fda50-varsha-devxs-projects.vercel.app",
            "https://ai-early-warning-business-failure-d-dun.vercel.app",
            "https://ai-early-warning-business-fail.vercel.app"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from app.api.routes import router
    app.include_router(router)

    # Register demo routes (for testing without real PDFs)
    from app.api.demo_routes import demo_router
    app.include_router(demo_router)

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        }

    # Favicon endpoint
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(status_code=204)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
