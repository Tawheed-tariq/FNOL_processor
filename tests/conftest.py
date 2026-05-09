from __future__ import annotations

import io
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Minimal valid PDF bytes (real PDF structure)
MINIMAL_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
  /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (FNOL Test Document) Tj ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000370 00000 n
trailer << /Size 6 /Root 1 0 R >>
startxref
441
%%EOF"""

SAMPLE_ACORD_TEXT = """
AUTOMOBILE LOSS NOTICE
AGENCY: ABC Insurance Agency  DATE: 01/15/2024
CARRIER: State Farm Insurance  NAIC CODE: 25143
POLICY NUMBER: PA-123456789  LINE OF BUSINESS: Auto

INSURED
NAME OF INSURED: John Michael Doe
DATE OF BIRTH: 03/22/1985
INSURED'S MAILING ADDRESS: 123 Main Street, Springfield, IL 62701
PRIMARY PHONE: 217-555-0123

LOSS
LOCATION OF LOSS
STREET: 400 E Oak Avenue
CITY, STATE, ZIP: Springfield, IL 62702
COUNTRY: USA
POLICE OR FIRE DEPARTMENT CONTACTED: YES
REPORT NUMBER: SPD-2024-00123
DATE OF LOSS AND TIME: 01/14/2024  3:30 PM

DESCRIPTION OF ACCIDENT:
Insured was travelling northbound on Oak Avenue when a red sedan ran a stop sign
and struck the insured's vehicle on the driver's side door.

INSURED VEHICLE
VEH#: 1  YEAR: 2021  MAKE: Toyota  MODEL: Camry  BODY TYPE: Sedan
V.I.N.: 4T1BF1FK5CU123456
PLATE NUMBER: IL ABC123  STATE: IL

OWNER'S NAME AND ADDRESS: John Michael Doe (same as insured)
DRIVER'S NAME AND ADDRESS: John Michael Doe (same as owner)
RELATION TO INSURED: Self
DRIVER'S LICENSE NUMBER: D123456789012  STATE: IL
PURPOSE OF USE: Personal  USED WITH PERMISSION: Y

DESCRIBE DAMAGE: Driver side door severely dented, window shattered,
airbag deployed. Front quarter panel also damaged.
ESTIMATE AMOUNT: 8500.00
WHERE CAN VEHICLE BE SEEN?: ABC Auto Body, 789 Repair Lane, Springfield IL
WHEN CAN VEHICLE BE SEEN?: Mon-Fri 8am-5pm

1. WAS A STANDARD CHILD PASSENGER RESTRAINT SYSTEM INSTALLED? N
2. WAS THE CHILD SEAT IN USE? N
3. DID THE CHILD SEAT SUSTAIN DAMAGE? N

OTHER INSURANCE ON VEHICLE - CARRIER: None
"""

SAMPLE_EXTRACTED_CLAIM_DICT = {
    "policy": {
        "policy_number": "PA-123456789",
        "carrier": "State Farm Insurance",
        "naic_code": "25143",
        "line_of_business": "Auto",
        "insured_location_code": None,
        "agency_name": "ABC Insurance Agency",
        "agency_code": None,
    },
    "insured": {
        "name": "John Michael Doe",
        "date_of_birth": "03/22/1985",
        "mailing_address": "123 Main Street, Springfield, IL 62701",
        "primary_phone": "217-555-0123",
        "email": None,
    },
    "contact": {
        "name": None,
        "mailing_address": None,
        "primary_phone": None,
        "email": None,
        "when_to_contact": None,
    },
    "incident": {
        "date_of_loss": "01/14/2024",
        "time_of_loss": "3:30 PM",
        "location_street": "400 E Oak Avenue",
        "location_city_state_zip": "Springfield, IL 62702",
        "location_country": "USA",
        "police_contacted": True,
        "report_number": "SPD-2024-00123",
        "description": "Insured was travelling northbound on Oak Avenue when a red sedan ran a stop sign and struck the insured's vehicle on the driver's side door.",
        "incident_type": "Collision",
    },
    "vehicle": {
        "veh_number": "1",
        "year": "2021",
        "make": "Toyota",
        "model": "Camry",
        "body_type": "Sedan",
        "vin": "4T1BF1FK5CU123456",
        "plate_number": "ABC123",
        "plate_state": "IL",
        "damage_description": "Driver side door severely dented, window shattered, airbag deployed.",
        "estimate_amount": 8500.00,
        "where_can_be_seen": "ABC Auto Body, 789 Repair Lane, Springfield IL",
        "when_can_be_seen": "Mon-Fri 8am-5pm",
        "other_insurance_carrier": None,
        "other_insurance_policy": None,
    },
    "owner": {
        "name": "John Michael Doe",
        "address": "123 Main Street, Springfield, IL 62701",
        "primary_phone": "217-555-0123",
        "email": None,
        "same_as_insured": True,
    },
    "driver": {
        "name": "John Michael Doe",
        "address": "123 Main Street, Springfield, IL 62701",
        "primary_phone": "217-555-0123",
        "email": None,
        "date_of_birth": "03/22/1985",
        "license_number": "D123456789012",
        "license_state": "IL",
        "relation_to_insured": "Self",
        "purpose_of_use": "Personal",
        "used_with_permission": True,
        "same_as_owner": True,
    },
    "child_seat": {"installed": False, "in_use_by_child": False, "sustained_loss": False},
    "third_party_vehicles": [],
    "injured_parties": [],
    "witnesses": [],
    "remarks": None,
}


# App client fixture
@pytest.fixture(scope="session")
def app_client() -> Generator:
    """TestClient with a mocked ClaimsProcessor to avoid Ollama dependency."""
    from app.main import app
    from app.api.dependencies import get_claims_processor

    mock_processor = _build_mock_processor()

    app.dependency_overrides[get_claims_processor] = lambda: mock_processor
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _build_mock_processor():
    """Build a mock ClaimsProcessor that returns a realistic response."""
    from app.models.schemas import (
        ClaimProcessingResponse,
        ClaimRoute,
        ExtractedClaim,
        ProcessingMetadata,
        RoutingDecision,
        ValidationReport,
    )
    from datetime import datetime
    import json

    mock = MagicMock()

    claim = ExtractedClaim.model_validate(SAMPLE_EXTRACTED_CLAIM_DICT)
    claim.raw_llm_output = json.dumps(SAMPLE_EXTRACTED_CLAIM_DICT)[:200]

    mock.process.return_value = ClaimProcessingResponse(
        claim_id="test-claim-uuid-1234",
        status="success",
        extracted_claim=claim,
        validation=ValidationReport(
            is_valid=True,
            missing_required_fields=[],
            issues=[],
            completeness_score=0.85,
        ),
        routing=RoutingDecision(
            route=ClaimRoute.MANUAL_REVIEW,
            reasoning="Damage estimate $8,500 is moderate; all required fields present.",
            priority_score=5,
            flags=["HIGH_VALUE_CLAIM: $8,500"],
        ),
        metadata=ProcessingMetadata(
            filename="test.pdf",
            file_size_bytes=len(MINIMAL_PDF_BYTES),
            pages_extracted=1,
            characters_extracted=500,
            processing_time_ms=1234.5,
            llm_model="llama3",
            processed_at=datetime(2024, 1, 15, 12, 0, 0),
        ),
    )
    return mock


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    return MINIMAL_PDF_BYTES


@pytest.fixture
def sample_acord_text() -> str:
    return SAMPLE_ACORD_TEXT


@pytest.fixture
def sample_claim_dict() -> dict:
    return SAMPLE_EXTRACTED_CLAIM_DICT