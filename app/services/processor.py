"""
Claims Processor Orchestration layer

Ties together Ingestion -> Extraction -> Validation -> Routing
into a single synchronous pipeline call.

Designed to be injected as a FastAPI dependency.
"""

from __future__ import annotations

import logging
import time
import uuid

from app.core.config import settings
from app.models.schemas import (
    ClaimProcessingResponse,
    ProcessingMetadata,
)
from app.services.extraction import LLMExtractionService
from app.services.ingestion import DocumentIngestionService
from app.services.routing import RoutingEngine
from app.services.validation import ValidationService

logger = logging.getLogger(__name__)


class ClaimsProcessor:
    """
    High-level orchestrator for the FNOL processing pipeline.

    Usage (FastAPI dependency injection):
        processor = ClaimsProcessor()
        result = processor.process(filename, file_bytes)
    """

    def __init__(self):
        self._ingestion = DocumentIngestionService()
        self._extraction = LLMExtractionService()
        self._validation = ValidationService()
        self._routing = RoutingEngine()

    def process(self, filename: str, content: bytes) -> ClaimProcessingResponse:
        """
        Full pipeline: PDF bytes -> structured ClaimProcessingResponse.

        Raises domain exceptions from each service layer; callers are
        responsible for translating these into HTTP responses.
        """
        claim_id = str(uuid.uuid4())
        pipeline_start = time.perf_counter()

        logger.info("[%s] Starting pipeline for '%s'", claim_id, filename)

        # Stage 1: Ingest
        t0 = time.perf_counter()
        document = self._ingestion.ingest(filename, content)
        logger.info("[%s] Ingestion: %.1f ms", claim_id, (time.perf_counter() - t0) * 1000)

        # Stage 2: Extract
        t0 = time.perf_counter()
        claim = self._extraction.extract(document)
        logger.info("[%s] Extraction: %.1f ms", claim_id, (time.perf_counter() - t0) * 1000)

        # Stage 3: Validate
        t0 = time.perf_counter()
        validation = self._validation.validate(claim)
        logger.info("[%s] Validation: %.1f ms", claim_id, (time.perf_counter() - t0) * 1000)

        # Stage 4: Route
        t0 = time.perf_counter()
        routing = self._routing.route(claim, validation)
        logger.info("[%s] Routing → %s (priority=%d): %.1f ms",
                    claim_id, routing.route, routing.priority_score,
                    (time.perf_counter() - t0) * 1000)

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        logger.info("[%s] Pipeline complete in %.1f ms", claim_id, total_ms)

        status = "success" if validation.is_valid else "partial"

        return ClaimProcessingResponse(
            claim_id=claim_id,
            status=status,
            extracted_claim=claim,
            validation=validation,
            routing=routing,
            metadata=ProcessingMetadata(
                filename=document.filename,
                file_size_bytes=document.file_size_bytes,
                pages_extracted=document.pages,
                characters_extracted=document.total_characters,
                processing_time_ms=round(total_ms, 2),
                llm_model=settings.OLLAMA_MODEL,
            ),
        )