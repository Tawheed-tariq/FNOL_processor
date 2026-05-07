"""Health & readiness endpoints."""

import logging

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", summary="Basic liveness check")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@router.get("/health/ready", summary="Readiness check – verifies Ollama reachability")
async def readiness():
    """
    Returns 200 if the service is ready to process claims (Ollama reachable),
    503 otherwise.
    """
    ollama_ok = False
    ollama_detail = ""

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ollama_ok = resp.status_code == 200
            if ollama_ok:
                tags = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in tags]
                ollama_detail = f"reachable; available models: {model_names}"
            else:
                ollama_detail = f"HTTP {resp.status_code}"
    except Exception as exc:
        ollama_detail = str(exc)

    payload = {
        "status": "ready" if ollama_ok else "degraded",
        "ollama": {"ok": ollama_ok, "detail": ollama_detail},
        "configured_model": settings.OLLAMA_MODEL,
    }
    code = 200 if ollama_ok else 503
    return JSONResponse(content=payload, status_code=code)