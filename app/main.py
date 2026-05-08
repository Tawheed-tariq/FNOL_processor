"""
FNOL Insurance Claims Processing System
Main FastAPI application entry point.
"""

import logging
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import claims, health
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

os.environ["OLLAMA_NO_GPU"] = "1" if settings.OLLAMA_NO_GPU else "0"
os.environ["OLLAMA_NUM_CTX"] = str(settings.OLLAMA_NUM_CTX)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FNOL Claims Processing System v%s", settings.APP_VERSION)
    logger.info("Ollama endpoint: %s | Model: %s", settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)
    yield
    logger.info("Shutting down FNOL Claims Processing System")


app = FastAPI(
    title="FNOL Insurance Claims Processing API",
    description=(
        "AI-powered First Notice of Loss (FNOL) document processing system. "
        "Extracts structured data from insurance claim PDFs and routes claims intelligently."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    logger.info("← %s %s %.1fms", request.method, request.url.path, duration)
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please check server logs."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["Claims"])