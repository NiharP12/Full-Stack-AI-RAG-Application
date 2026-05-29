"""
FastAPI application factory.
Configures CORS, middleware, exception handlers, and lifespan events.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging_config import setup_logging

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: initialise resources on startup, clean up on shutdown."""
    # --- Startup ---
    setup_logging(log_level=settings.log_level, log_file=settings.log_file)
    logger = logging.getLogger(__name__)
    logger.info("Starting RAG Application backend …")

    # Ensure required directories exist
    settings.ensure_directories()

    # Pre-load the embedding model so first query is fast
    try:
        from app.rag.embeddings import get_embedding_model
        get_embedding_model()
        logger.info("Embedding model loaded successfully")
    except Exception as exc:
        logger.warning("Could not pre-load embedding model: %s", exc)

    # Initialise the vector store if an index already exists on disk
    try:
        from app.rag.vectorstore import VectorStoreManager
        vs = VectorStoreManager()
        vs.load_or_create()
        logger.info("Vector store ready")
    except Exception as exc:
        logger.warning("Could not initialise vector store: %s", exc)

    yield  # ← application is running

    # --- Shutdown ---
    logger.info("Shutting down RAG Application backend")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RAG Application API",
        description="Retrieval-Augmented Generation backend — upload documents, ask questions, get cited answers.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Request logging middleware ---
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start
        logger = logging.getLogger("http")
        logger.info(
            "%s %s — %s (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response

    # --- Global exception handler ---
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger = logging.getLogger("http")
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later."},
        )

    # --- Register routers ---
    from app.api.routes import health, upload, chat, documents, history

    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(upload.router, prefix="/api", tags=["Upload"])
    app.include_router(chat.router, prefix="/api", tags=["Chat"])
    app.include_router(documents.router, prefix="/api", tags=["Documents"])
    app.include_router(history.router, prefix="/api", tags=["History"])

    return app


# Create the application instance
app = create_app()
