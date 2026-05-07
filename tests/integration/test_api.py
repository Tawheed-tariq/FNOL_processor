"""
Integration tests – FastAPI endpoints
Uses TestClient with a mocked ClaimsProcessor (no Ollama required).
"""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import MINIMAL_PDF_BYTES


class TestHealthEndpoints:
    def test_health_returns_200(self, app_client):
        resp = app_client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "version" in body

    def test_readiness_endpoint_exists(self, app_client):
        # Readiness calls Ollama; in test env it will be 503 (no Ollama running)
        resp = app_client.get("/api/v1/health/ready")
        assert resp.status_code in (200, 503)
        body = resp.json()
        assert "status" in body
        assert "ollama" in body


class TestProcessSingleClaim:
    def test_valid_pdf_returns_200(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("test.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        assert resp.status_code == 200

    def test_response_contains_required_keys(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("test.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        body = resp.json()
        assert "claim_id" in body
        assert "status" in body
        assert "extracted_claim" in body
        assert "validation" in body
        assert "routing" in body
        assert "metadata" in body

    def test_extracted_claim_has_policy(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("test.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        body = resp.json()
        assert "policy" in body["extracted_claim"]
        assert "policy_number" in body["extracted_claim"]["policy"]

    def test_routing_decision_has_route_and_reasoning(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("test.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        routing = resp.json()["routing"]
        assert "route" in routing
        assert "reasoning" in routing
        assert "priority_score" in routing
        assert isinstance(routing["priority_score"], int)
        assert 1 <= routing["priority_score"] <= 10

    def test_validation_report_structure(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("test.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        val = resp.json()["validation"]
        assert "is_valid" in val
        assert "missing_required_fields" in val
        assert "issues" in val
        assert "completeness_score" in val

    def test_metadata_contains_filename(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("my_claim.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        meta = resp.json()["metadata"]
        assert "filename" in meta
        assert "processing_time_ms" in meta
        assert "llm_model" in meta

    def test_no_file_returns_422(self, app_client):
        resp = app_client.post("/api/v1/claims/process")
        assert resp.status_code == 422

    def test_non_pdf_file_returns_error(self, app_client):
        """When processor raises UnsupportedFileTypeError it should 422."""
        from app.core.exceptions import UnsupportedFileTypeError
        from app.api.dependencies import get_claims_processor
        from app.main import app

        mock_proc = MagicMock()
        mock_proc.process.side_effect = UnsupportedFileTypeError("Not a PDF")
        app.dependency_overrides[get_claims_processor] = lambda: mock_proc

        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("doc.txt", b"just some text", "text/plain")},
        )
        # Reset override
        from tests.conftest import _build_mock_processor
        app.dependency_overrides[get_claims_processor] = lambda: _build_mock_processor()

        assert resp.status_code == 422

    def test_llm_unavailable_returns_503(self, app_client):
        from app.core.exceptions import LLMUnavailableError
        from app.api.dependencies import get_claims_processor
        from app.main import app

        mock_proc = MagicMock()
        mock_proc.process.side_effect = LLMUnavailableError("Ollama not running")
        app.dependency_overrides[get_claims_processor] = lambda: mock_proc

        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("test.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
        )
        from tests.conftest import _build_mock_processor
        app.dependency_overrides[get_claims_processor] = lambda: _build_mock_processor()

        assert resp.status_code == 503

    def test_large_file_rejected(self, app_client):
        from app.core.exceptions import FileSizeLimitError
        from app.api.dependencies import get_claims_processor
        from app.main import app

        mock_proc = MagicMock()
        mock_proc.process.side_effect = FileSizeLimitError("File too large")
        app.dependency_overrides[get_claims_processor] = lambda: mock_proc

        big_content = b"%PDF" + b"x" * (21 * 1024 * 1024)
        resp = app_client.post(
            "/api/v1/claims/process",
            files={"file": ("big.pdf", big_content, "application/pdf")},
        )
        from tests.conftest import _build_mock_processor
        app.dependency_overrides[get_claims_processor] = lambda: _build_mock_processor()

        assert resp.status_code in (413, 422)


class TestBatchProcessing:
    def test_batch_single_file_succeeds(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/batch",
            files=[("files", ("a.pdf", MINIMAL_PDF_BYTES, "application/pdf"))],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["succeeded"] == 1
        assert body["failed"] == 0

    def test_batch_multiple_files(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/batch",
            files=[
                ("files", ("a.pdf", MINIMAL_PDF_BYTES, "application/pdf")),
                ("files", ("b.pdf", MINIMAL_PDF_BYTES, "application/pdf")),
            ],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2

    def test_batch_response_has_items(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/batch",
            files=[("files", ("a.pdf", MINIMAL_PDF_BYTES, "application/pdf"))],
        )
        body = resp.json()
        assert "items" in body
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert "filename" in item
        assert "status" in item

    def test_batch_no_files_returns_422(self, app_client):
        resp = app_client.post("/api/v1/claims/batch")
        assert resp.status_code == 422

    def test_batch_returns_processing_time(self, app_client):
        resp = app_client.post(
            "/api/v1/claims/batch",
            files=[("files", ("a.pdf", MINIMAL_PDF_BYTES, "application/pdf"))],
        )
        body = resp.json()
        assert "batch_processing_time_ms" in body
        assert body["batch_processing_time_ms"] >= 0


class TestSupportedRoutes:
    def test_returns_all_four_routes(self, app_client):
        resp = app_client.get("/api/v1/claims/supported-routes")
        assert resp.status_code == 200
        body = resp.json()
        assert "routes" in body
        route_names = [r["name"] for r in body["routes"]]
        assert "Fast-track" in route_names
        assert "Manual Review" in route_names
        assert "Investigation" in route_names
        assert "Specialist Queue" in route_names

    def test_each_route_has_description_and_sla(self, app_client):
        resp = app_client.get("/api/v1/claims/supported-routes")
        for route in resp.json()["routes"]:
            assert "description" in route
            assert "typical_sla" in route


class TestAPIDocumentation:
    def test_openapi_schema_accessible(self, app_client):
        resp = app_client.get("/openapi.json")
        assert resp.status_code == 200

    def test_swagger_ui_accessible(self, app_client):
        resp = app_client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_accessible(self, app_client):
        resp = app_client.get("/redoc")
        assert resp.status_code == 200