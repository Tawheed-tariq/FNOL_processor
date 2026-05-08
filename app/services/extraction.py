"""
LLM Extraction Service
----------------------
Uses a locally-running Ollama LLM to parse raw FNOL document text
and return a structured ExtractedClaim.

Design decisions:
- Uses a single, detailed system prompt with JSON schema embedded.
- Retries on transient failures (network blip, model loading).
- Falls back gracefully: if JSON parse fails, returns an empty claim
  with the raw response attached for debugging.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import LLMExtractionError, LLMUnavailableError
from app.models.schemas import (
    ChildSeatInfo,
    ContactParty,
    DriverDetails,
    ExtractedClaim,
    IncidentDetails,
    IncidentType,
    InsuredParty,
    InjuredParty,
    OwnerDetails,
    PolicyInformation,
    ThirdPartyVehicle,
    VehicleDetails,
    Witness,
)
from app.services.ingestion import ExtractedDocument

logger = logging.getLogger(__name__)

# ── Prompt template ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert insurance document parser specialising in ACORD FNOL (First Notice of Loss) forms.
Your task is to extract ALL available structured information from the provided document text and return ONLY a valid JSON object.

STRICT RULES:
1. Return ONLY the JSON object — no markdown, no explanation, no code fences.
2. If a field is not found, set it to null.
3. Boolean fields: use true/false (JSON booleans), never strings.
4. Monetary amounts: extract as a number (float), e.g. 2500.00 — no currency symbols.
5. Dates: preserve the original format from the document (e.g. MM/DD/YYYY).
6. For incident_type choose one of: Collision, Theft, Vandalism, Natural Disaster, Fire, Flood, Hit and Run, Other, Unknown.

JSON SCHEMA TO FILL:
{
  "policy": {
    "policy_number": null,
    "carrier": null,
    "naic_code": null,
    "line_of_business": null,
    "insured_location_code": null,
    "agency_name": null,
    "agency_code": null
  },
  "insured": {
    "name": null,
    "date_of_birth": null,
    "mailing_address": null,
    "primary_phone": null,
    "email": null
  },
  "contact": {
    "name": null,
    "mailing_address": null,
    "primary_phone": null,
    "email": null,
    "when_to_contact": null
  },
  "incident": {
    "date_of_loss": null,
    "time_of_loss": null,
    "location_street": null,
    "location_city_state_zip": null,
    "location_country": null,
    "police_contacted": null,
    "report_number": null,
    "description": null,
    "incident_type": "Unknown"
  },
  "vehicle": {
    "veh_number": null,
    "year": null,
    "make": null,
    "model": null,
    "body_type": null,
    "vin": null,
    "plate_number": null,
    "plate_state": null,
    "damage_description": null,
    "estimate_amount": null,
    "where_can_be_seen": null,
    "when_can_be_seen": null,
    "other_insurance_carrier": null,
    "other_insurance_policy": null
  },
  "owner": {
    "name": null,
    "address": null,
    "primary_phone": null,
    "email": null,
    "same_as_insured": false
  },
  "driver": {
    "name": null,
    "address": null,
    "primary_phone": null,
    "email": null,
    "date_of_birth": null,
    "license_number": null,
    "license_state": null,
    "relation_to_insured": null,
    "purpose_of_use": null,
    "used_with_permission": null,
    "same_as_owner": false
  },
  "child_seat": {
    "installed": null,
    "in_use_by_child": null,
    "sustained_loss": null
  },
  "third_party_vehicles": [],
  "injured_parties": [],
  "witnesses": [],
  "remarks": null
}"""


USER_PROMPT_TEMPLATE = """Extract all fields from the following FNOL document text. Return ONLY the filled JSON object.

--- DOCUMENT START ---
{document_text}
--- DOCUMENT END ---"""


class LLMExtractionService:
    """
    Calls Ollama's /api/chat endpoint to extract structured fields from FNOL text.

    Thread-safe: each call creates its own HTTP client (no shared state).
    """

    def __init__(self):
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._timeout = settings.OLLAMA_TIMEOUT
        self._max_retries = settings.OLLAMA_MAX_RETRIES

    # def extract(self, document: ExtractedDocument) -> ExtractedClaim:
    #     """
    #     Main entry point: takes an ExtractedDocument and returns an ExtractedClaim.

    #     Raises:
    #         LLMUnavailableError: if Ollama service cannot be reached
    #         LLMExtractionError:  if LLM returns unusable output after retries
    #     """
    #     text = document.raw_text[:12_000]  # Trim to ~3k tokens; most ACORD forms fit
    #     prompt = USER_PROMPT_TEMPLATE.format(document_text=text)
    #     logger.info(f"Document chars: {len(document.text)}")
    #     raw_response = self._call_llm_with_retries(prompt)
    #     return self._parse_response(raw_response)

    def extract(self, document: ExtractedDocument) -> ExtractedClaim:
        """
        Main entry point: takes an ExtractedDocument and returns an ExtractedClaim.

        Raises:
            LLMUnavailableError: if Ollama service cannot be reached
            LLMExtractionError:  if LLM returns unusable output after retries
        """

        # Original extracted text
        raw_text = document.raw_text

        # Logging
        logger.info(f"Document chars: {len(raw_text)}")
        logger.info(f"Approx tokens: {len(raw_text) // 4}")

        # Trim oversized PDFs
        text = raw_text[:12_000]

        logger.info(f"Trimmed chars: {len(text)}")
        logger.info(f"Prompt tokens est: {len(text) // 4}")

        # Build prompt
        prompt = USER_PROMPT_TEMPLATE.format(
            document_text=text
        )

        # Call LLM
        raw_response = self._call_llm_with_retries(prompt)

        # Parse structured response
        return self._parse_response(raw_response)

    # ── LLM communication ─────────────────────────────────────────────────────

    def _call_llm_with_retries(self, user_prompt: str) -> str:
        last_exc: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 2):  # +2 because range is exclusive
            try:
                return self._call_llm(user_prompt)
            except LLMUnavailableError:
                raise  # Don't retry on connectivity failures
            except LLMExtractionError as exc:
                last_exc = exc
                logger.warning("LLM attempt %d/%d failed: %s", attempt, self._max_retries + 1, exc)
                if attempt <= self._max_retries:
                    time.sleep(1.5 * attempt)

        raise LLMExtractionError(
            f"LLM extraction failed after {self._max_retries + 1} attempts. "
            f"Last error: {last_exc}"
        )

    def _call_llm(self, user_prompt: str) -> str:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,   # Deterministic extraction
                "num_predict": 4096,
            },
        }

        logger.debug("Calling Ollama at %s with model '%s'", url, self._model)
        t0 = time.perf_counter()

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMUnavailableError(
                f"Cannot reach Ollama at '{self._base_url}'. "
                f"Ensure Ollama is running: 'ollama serve'. Error: {exc}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMExtractionError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMExtractionError(
                f"Ollama request timed out after {self._timeout}s. "
                "Consider increasing OLLAMA_TIMEOUT or using a smaller model."
            ) from exc

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("Ollama responded in %.1f ms", elapsed)

        data = resp.json()
        content = (
            data.get("message", {}).get("content", "")
            or data.get("response", "")
        )
        if not content:
            raise LLMExtractionError("Ollama returned an empty message content.")
        return content

    # ── Response parsing ──────────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> ExtractedClaim:
        """
        Parse the LLM's raw text output into an ExtractedClaim.
        Handles markdown fences and trailing garbage gracefully.
        """
        cleaned = self._strip_markdown(raw)

        try:
            data: Dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to recover by finding the first complete JSON object
            data = self._recover_json(cleaned)
            if data is None:
                logger.error("Could not parse LLM output as JSON. Raw: %.500s", raw)
                # Return empty claim with raw output for debugging
                claim = ExtractedClaim()
                claim.raw_llm_output = raw[:2000]
                return claim

        claim = self._map_to_claim(data)
        claim.raw_llm_output = raw[:500]  # Store a snippet for traceability
        return claim

    def _strip_markdown(self, text: str) -> str:
        """Remove ```json ... ``` fences and leading/trailing whitespace."""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
        return text.strip()

    def _recover_json(self, text: str) -> Optional[Dict]:
        """Best-effort JSON recovery: find first '{' ... last '}'."""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return None

    def _map_to_claim(self, data: Dict[str, Any]) -> ExtractedClaim:
        """
        Map a loosely-typed dict (from LLM) to strongly-typed Pydantic models.
        Each sub-model uses .model_validate() with strict=False so extra/missing
        keys are handled gracefully.
        """
        def safe(klass, raw):
            if not isinstance(raw, dict):
                return klass()
            try:
                return klass.model_validate(raw)
            except Exception:
                return klass()

        def safe_list(klass, raw):
            if not isinstance(raw, list):
                return []
            result = []
            for item in raw:
                try:
                    result.append(klass.model_validate(item))
                except Exception:
                    pass
            return result

        # Normalise incident_type enum
        incident_raw = data.get("incident", {}) or {}
        it_str = incident_raw.get("incident_type", "Unknown")
        try:
            incident_raw["incident_type"] = IncidentType(it_str)
        except ValueError:
            incident_raw["incident_type"] = IncidentType.UNKNOWN

        return ExtractedClaim(
            policy=safe(PolicyInformation, data.get("policy")),
            insured=safe(InsuredParty, data.get("insured")),
            contact=safe(ContactParty, data.get("contact")),
            incident=safe(IncidentDetails, incident_raw),
            vehicle=safe(VehicleDetails, data.get("vehicle")),
            owner=safe(OwnerDetails, data.get("owner")),
            driver=safe(DriverDetails, data.get("driver")),
            child_seat=safe(ChildSeatInfo, data.get("child_seat")),
            third_party_vehicles=safe_list(ThirdPartyVehicle, data.get("third_party_vehicles")),
            injured_parties=safe_list(InjuredParty, data.get("injured_parties")),
            witnesses=safe_list(Witness, data.get("witnesses")),
            remarks=data.get("remarks"),
        )