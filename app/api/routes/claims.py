"""
Claims API Routes
-----------------
POST /api/v1/claims/process        – process a single FNOL PDF
POST /api/v1/claims/batch          – process up to MAX_BATCH_SIZE PDFs
GET  /api/v1/claims/supported-routes – list available claim routes
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_claims_processor
from app.core.config import settings
from app.core.exceptions import (
    DocumentIngestionError,
    FileSizeLimitError,
    LLMUnavailableError,
    UnsupportedFileTypeError,
)
from app.models.schemas import (
    BatchProcessingItem,
    BatchProcessingResponse,
    ClaimProcessingResponse,
    ClaimRoute,
)
from app.services.processor import ClaimsProcessor

logger = logging.getLogger(__name__)
router = APIRouter()
llm_semaphore = asyncio.Semaphore(1)

# Thread pool for CPU/IO bound LLM calls (keeps the async event loop free)
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fnol-worker")


def _run_in_thread(processor: ClaimsProcessor, filename: str, content: bytes):
    """Blocking pipeline call – runs in a thread pool worker."""
    return processor.process(filename, content)


async def _read_upload(upload: UploadFile) -> bytes:
    """Read UploadFile bytes with size guard."""
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await upload.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{upload.filename}' exceeds the {settings.MAX_FILE_SIZE_MB} MB limit.",
        )
    return content


def _map_exception_to_http(exc: Exception, filename: str) -> HTTPException:
    """Convert domain exceptions to appropriate HTTP errors."""
    if isinstance(exc, (UnsupportedFileTypeError, FileSizeLimitError)):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, DocumentIngestionError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, LLMUnavailableError):
        return HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {exc}. Ensure Ollama is running.",
        )
    logger.exception("Unexpected error processing '%s'", filename)
    return HTTPException(status_code=500, detail=f"Processing failed for '{filename}': {exc}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/process",
    response_model=ClaimProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a single FNOL PDF",
    response_description="Structured claim data with validation report and routing decision",
)
async def process_single_claim(
    file: UploadFile = File(..., description="FNOL PDF document (max 20 MB)"),
    processor: ClaimsProcessor = Depends(get_claims_processor),
):
    """
    Upload a single FNOL PDF for AI-powered field extraction and routing.

    - **Extracts** all structured fields from the document via a local LLM (Ollama)
    - **Validates** completeness and consistency of extracted data
    - **Routes** the claim to: Fast-track | Manual Review | Investigation | Specialist Queue
    """
    content = await _read_upload(file)

    loop = asyncio.get_event_loop()
    try:
        # result = await loop.run_in_executor(
        #     _executor, _run_in_thread, processor, file.filename, content
        # )
        async with llm_semaphore:
            result = await loop.run_in_executor(
                 _executor, _run_in_thread, processor, file.filename, content
            )
    except Exception as exc:
        raise _map_exception_to_http(exc, file.filename) from exc

    return result


@router.post(
    "/batch",
    response_model=BatchProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch-process multiple FNOL PDFs",
)
async def process_batch_claims(
    files: List[UploadFile] = File(..., description=f"Up to {settings.MAX_BATCH_SIZE} FNOL PDFs"),
    processor: ClaimsProcessor = Depends(get_claims_processor),
):
    """
    Upload up to **{MAX_BATCH_SIZE}** FNOL PDFs for parallel processing.
    Returns an aggregated result with per-file success/failure status.
    """
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required.")

    if len(files) > settings.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum batch size is {settings.MAX_BATCH_SIZE}. Received {len(files)} files.",
        )

    batch_start = time.perf_counter()
    loop = asyncio.get_event_loop()
    items: List[BatchProcessingItem] = []

    # Read all files concurrently
    contents = await asyncio.gather(
        *[_read_upload(f) for f in files],
        return_exceptions=True,
    )

    # Process each file (CPU/IO bound – use thread pool)
    async def _process_one(upload: UploadFile, content_or_exc) -> BatchProcessingItem:
        if isinstance(content_or_exc, Exception):
            return BatchProcessingItem(
                filename=upload.filename,
                status="error",
                error=str(content_or_exc),
            )
        try:
            result = await loop.run_in_executor(
                _executor, _run_in_thread, processor, upload.filename, content_or_exc
            )
            return BatchProcessingItem(
                filename=upload.filename,
                claim_id=result.claim_id,
                status="success",
                response=result,
            )
        except Exception as exc:
            logger.warning("Batch item '%s' failed: %s", upload.filename, exc)
            return BatchProcessingItem(
                filename=upload.filename,
                status="error",
                error=str(exc),
            )

    tasks = [_process_one(f, c) for f, c in zip(files, contents)]
    items = await asyncio.gather(*tasks)

    succeeded = sum(1 for i in items if i.status == "success")
    failed = len(items) - succeeded

    return BatchProcessingResponse(
        total=len(items),
        succeeded=succeeded,
        failed=failed,
        items=items,
        batch_processing_time_ms=round((time.perf_counter() - batch_start) * 1000, 2),
    )


@router.get(
    "/supported-routes",
    summary="List all supported claim routing categories",
)
async def get_supported_routes():
    """Returns all routing categories with descriptions."""
    return {
        "routes": [
            {
                "name": ClaimRoute.FAST_TRACK,
                "description": "Simple, complete, low-value claims processed automatically.",
                "typical_sla": "Same business day",
            },
            {
                "name": ClaimRoute.MANUAL_REVIEW,
                "description": "Claims with missing fields or minor inconsistencies requiring adjuster review.",
                "typical_sla": "1–2 business days",
            },
            {
                "name": ClaimRoute.INVESTIGATION,
                "description": "High-value claims, suspected fraud, or unauthorised vehicle use.",
                "typical_sla": "3–10 business days",
            },
            {
                "name": ClaimRoute.SPECIALIST_QUEUE,
                "description": "Bodily injury, catastrophic events, child seat damage, or multi-party incidents.",
                "typical_sla": "2–5 business days",
            },
        ]
    }