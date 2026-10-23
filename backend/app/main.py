"""DocuGraph RAG Backend - FastAPI Application Entry Point"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.services.neo4j_service import init_neo4j
from app.routers import notebooks, sources, chat, graph, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──
    logger.info("🚀 Starting DocuGraph RAG Backend...")

    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Upload directory: {upload_dir.absolute()}")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Initialize Neo4j constraints & indices
    init_neo4j()
    logger.info("✅ Neo4j database initialized")

    # Verify Gemini API key
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.warning("⚠️  GEMINI_API_KEY not set! AI features will not work.")
    else:
        logger.info("✅ Gemini API key configured")

    logger.info("✅ DocuGraph RAG Backend ready!")

    yield

    # ── Shutdown ──
    logger.info("👋 Shutting down DocuGraph RAG Backend...")


# Create FastAPI app
app = FastAPI(
    title="DocuGraph RAG API",
    description="RAG-powered document intelligence & Knowledge Graph backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(notebooks.router)
app.include_router(sources.router)
app.include_router(chat.router)
app.include_router(graph.router)


# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "notebooklm-backend",
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    return {
        "message": "NotebookLM Clone API",
        "docs": "/docs",
        "health": "/api/health",
    }
