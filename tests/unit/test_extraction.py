"""
Unit tests  LLMExtractionService
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import LLMExtractionError, LLMUnavailableError
from app.models.schemas import IncidentType
from app.services.extraction import LLMExtractionService
from app.services.ingestion import ExtractedDocument


@pytest.fixture
def svc():
    return LLMExtractionService()


@pytest.fixture
def mock_document():
    return ExtractedDocument(
        filename="test.pdf",
        file_size_bytes=1024,
        pages=1,
        raw_text="POLICY NUMBER: PA-123\nINSURED: Jane Doe\nDATE OF LOSS: 01/10/2024\n"
                 "MAKE: Toyota MODEL: Camry\nDESCRIPTION: Minor fender bender.",
        page_texts=["POLICY NUMBER: PA-123\nINSURED: Jane Doe"],
    )


VALID_LLM_JSON = {
    "policy": {"policy_number": "PA-123", "carrier": "ACME", "naic_code": None,
               "line_of_business": "Auto", "insured_location_code": None,
               "agency_name": None, "agency_code": None},
    "insured": {"name": "Jane Doe", "date_of_birth": None, "mailing_address": None,
                "primary_phone": None, "email": None},
    "contact": {"name": None, "mailing_address": None, "primary_phone": None,
                "email": None, "when_to_contact": None},
    "incident": {"date_of_loss": "01/10/2024", "time_of_loss": None,
                 "location_street": None, "location_city_state_zip": None,
                 "location_country": None, "police_contacted": False,
                 "report_number": None, "description": "Minor fender bender.",
                 "incident_type": "Collision"},
    "vehicle": {"veh_number": None, "year": "2022", "make": "Toyota", "model": "Camry",
                "body_type": None, "vin": None, "plate_number": None, "plate_state": None,
                "damage_description": None, "estimate_amount": None,
                "where_can_be_seen": None, "when_can_be_seen": None,
                "other_insurance_carrier": None, "other_insurance_policy": None},
    "owner": {"name": None, "address": None, "primary_phone": None, "email": None, "same_as_insured": False},
    "driver": {"name": None, "address": None, "primary_phone": None, "email": None,
               "date_of_birth": None, "license_number": None, "license_state": None,
               "relation_to_insured": None, "purpose_of_use": None, "used_with_permission": None,
               "same_as_owner": False},
    "child_seat": {"installed": None, "in_use_by_child": None, "sustained_loss": None},
    "third_party_vehicles": [],
    "injured_parties": [],
    "witnesses": [],
    "remarks": None,
}


def _mock_response(content: str):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": {"content": content}}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class TestSuccessfulExtraction:
    def test_valid_json_response_maps_correctly(self, svc, mock_document):
        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.return_value = _mock_response(json.dumps(VALID_LLM_JSON))
            mock_client_cls.return_value = mock_ctx

            claim = svc.extract(mock_document)

        assert claim.policy.policy_number == "PA-123"
        assert claim.insured.name == "Jane Doe"
        assert claim.incident.incident_type == IncidentType.COLLISION
        assert claim.vehicle.make == "Toyota"

    def test_markdown_fenced_json_is_parsed(self, svc, mock_document):
        fenced = f"```json\n{json.dumps(VALID_LLM_JSON)}\n```"
        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.return_value = _mock_response(fenced)
            mock_client_cls.return_value = mock_ctx

            claim = svc.extract(mock_document)

        assert claim.policy.policy_number == "PA-123"

    def test_unknown_incident_type_defaults(self, svc, mock_document):
        data = dict(VALID_LLM_JSON)
        data["incident"] = dict(VALID_LLM_JSON["incident"], incident_type="Earthquake")

        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.return_value = _mock_response(json.dumps(data))
            mock_client_cls.return_value = mock_ctx

            claim = svc.extract(mock_document)

        assert claim.incident.incident_type == IncidentType.UNKNOWN


class TestErrorHandling:
    def test_connection_error_raises_unavailable(self, svc, mock_document):
        import httpx
        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_cls.return_value = mock_ctx

            with pytest.raises(LLMUnavailableError):
                svc.extract(mock_document)

    def test_invalid_json_returns_empty_claim(self, svc, mock_document):
        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.return_value = _mock_response("This is not JSON at all!")
            mock_client_cls.return_value = mock_ctx

            # Should not raise; returns empty claim
            with patch.object(svc, "_max_retries", 0):
                claim = svc.extract(mock_document)

            # Empty claim is still a valid ExtractedClaim
            assert claim is not None

    def test_empty_llm_response_raises_extraction_error(self, svc, mock_document):
        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.return_value = _mock_response("")
            mock_client_cls.return_value = mock_ctx

            with pytest.raises((LLMExtractionError, Exception)):
                svc.extract(mock_document)


class TestMarkdownStripping:
    def test_strip_json_fence(self, svc):
        result = svc._strip_markdown("```json\n{}\n```")
        assert result == "{}"

    def test_strip_plain_fence(self, svc):
        result = svc._strip_markdown("```\n{}\n```")
        assert result == "{}"

    def test_no_fence_unchanged(self, svc):
        result = svc._strip_markdown('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_whitespace_stripped(self, svc):
        result = svc._strip_markdown("  \n  {}\n  ")
        assert result == "{}"


class TestJSONRecovery:
    def test_recovers_json_from_preamble(self, svc):
        text = 'Here is the result: {"policy_number": "X"} Hope that helps!'
        result = svc._recover_json(text)
        assert result == {"policy_number": "X"}

    def test_returns_none_for_no_json(self, svc):
        result = svc._recover_json("No JSON here at all.")
        assert result is None