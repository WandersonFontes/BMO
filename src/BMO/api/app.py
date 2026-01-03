from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.BMO.api.routes import router as v1_router
from src.BMO.config.settings import settings

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="BMO API",
        description="Modular AI Assistant API Layer",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Adjust for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(v1_router, prefix="/v1", tags=["BMO V1"])

    @app.on_event("startup")
    async def startup_event():
        logger = logging.getLogger("src.BMO.api")
        logger.info("BMO API is starting up...")
        # Pre-build graph to warm up on startup
        from src.BMO.core.orchestrator import get_compiled_graph
        get_compiled_graph()

    return app

app = create_app()
