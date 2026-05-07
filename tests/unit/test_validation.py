"""
Unit tests – ValidationService
"""

import pytest
from app.models.schemas import (
    ChildSeatInfo,
    ExtractedClaim,
    IncidentDetails,
    IncidentType,
    InsuredParty,
    PolicyInformation,
    ValidationSeverity,
    VehicleDetails,
)
from app.services.validation import ValidationService


@pytest.fixture
def svc():
    return ValidationService()


def _make_claim(**overrides) -> ExtractedClaim:
    """Build a minimally valid ExtractedClaim."""
    claim = ExtractedClaim()
    claim.policy = PolicyInformation(policy_number="PA-999")
    claim.insured = InsuredParty(name="Jane Doe", primary_phone="2175550001")
    claim.incident = IncidentDetails(
        date_of_loss="01/10/2024",
        description="Rear-ended at traffic light.",
        incident_type=IncidentType.COLLISION,
    )
    claim.vehicle = VehicleDetails(
        make="Honda",
        model="Civic",
        vin="1HGCM82633A123456",
        estimate_amount=3000.0,
    )
    for k, v in overrides.items():
        setattr(claim, k, v)
    return claim


class TestRequiredFieldValidation:
    def test_valid_claim_passes(self, svc):
        report = svc.validate(_make_claim())
        assert report.is_valid is True
        assert report.missing_required_fields == []

    def test_missing_policy_number_fails(self, svc):
        claim = _make_claim()
        claim.policy.policy_number = None
        report = svc.validate(claim)
        assert report.is_valid is False
        assert "policy.policy_number" in report.missing_required_fields

    def test_missing_insured_name_fails(self, svc):
        claim = _make_claim()
        claim.insured.name = None
        report = svc.validate(claim)
        assert not report.is_valid
        assert "insured.name" in report.missing_required_fields

    def test_missing_date_of_loss_fails(self, svc):
        claim = _make_claim()
        claim.incident.date_of_loss = None
        report = svc.validate(claim)
        assert not report.is_valid

    def test_multiple_missing_fields(self, svc):
        claim = ExtractedClaim()  # All None
        report = svc.validate(claim)
        assert not report.is_valid
        assert len(report.missing_required_fields) >= 4


class TestDateValidation:
    def test_future_date_produces_error(self, svc):
        claim = _make_claim()
        claim.incident.date_of_loss = "12/31/2099"
        report = svc.validate(claim)
        error_fields = [i.field for i in report.issues if i.severity == ValidationSeverity.ERROR]
        assert "incident.date_of_loss" in error_fields

    def test_unparseable_date_produces_warning(self, svc):
        claim = _make_claim()
        claim.incident.date_of_loss = "not-a-date"
        report = svc.validate(claim)
        warn_fields = [i.field for i in report.issues if i.severity == ValidationSeverity.WARNING]
        assert "incident.date_of_loss" in warn_fields

    def test_valid_date_no_date_issues(self, svc):
        claim = _make_claim()
        report = svc.validate(claim)
        date_issues = [i for i in report.issues if i.field == "incident.date_of_loss"]
        assert len(date_issues) == 0


class TestVINValidation:
    def test_valid_17char_vin_passes(self, svc):
        claim = _make_claim()
        claim.vehicle.vin = "1HGCM82633A123456"
        report = svc.validate(claim)
        vin_issues = [i for i in report.issues if i.field == "vehicle.vin"]
        assert len(vin_issues) == 0

    def test_short_vin_produces_warning(self, svc):
        claim = _make_claim()
        claim.vehicle.vin = "ABC123"
        report = svc.validate(claim)
        vin_issues = [i for i in report.issues if i.field == "vehicle.vin"]
        assert len(vin_issues) == 1
        assert vin_issues[0].severity == ValidationSeverity.WARNING

    def test_none_vin_no_vin_warning(self, svc):
        claim = _make_claim()
        claim.vehicle.vin = None
        report = svc.validate(claim)
        vin_format_issues = [
            i for i in report.issues
            if i.field == "vehicle.vin" and "17-character" in i.message
        ]
        assert len(vin_format_issues) == 0


class TestEstimateValidation:
    def test_negative_estimate_produces_error(self, svc):
        claim = _make_claim()
        claim.vehicle.estimate_amount = -100.0
        report = svc.validate(claim)
        err_fields = [i.field for i in report.issues if i.severity == ValidationSeverity.ERROR]
        assert "vehicle.estimate_amount" in err_fields

    def test_very_high_estimate_produces_warning(self, svc):
        claim = _make_claim()
        claim.vehicle.estimate_amount = 999_999.0
        report = svc.validate(claim)
        warn_fields = [i.field for i in report.issues if i.severity == ValidationSeverity.WARNING]
        assert "vehicle.estimate_amount" in warn_fields

    def test_normal_estimate_no_issue(self, svc):
        claim = _make_claim()
        claim.vehicle.estimate_amount = 5000.0
        report = svc.validate(claim)
        est_issues = [i for i in report.issues if i.field == "vehicle.estimate_amount"]
        assert len(est_issues) == 0


class TestChildSeatValidation:
    def test_inconsistent_child_seat_produces_error(self, svc):
        claim = _make_claim()
        claim.child_seat = ChildSeatInfo(installed=False, in_use_by_child=True, sustained_loss=None)
        report = svc.validate(claim)
        err_fields = [i.field for i in report.issues if i.severity == ValidationSeverity.ERROR]
        assert "child_seat.in_use_by_child" in err_fields

    def test_not_in_use_but_damaged_produces_warning(self, svc):
        claim = _make_claim()
        claim.child_seat = ChildSeatInfo(installed=True, in_use_by_child=False, sustained_loss=True)
        report = svc.validate(claim)
        warn_fields = [i.field for i in report.issues if i.severity == ValidationSeverity.WARNING]
        assert "child_seat.sustained_loss" in warn_fields


class TestCompletenessScore:
    def test_complete_claim_high_score(self, svc):
        claim = _make_claim()
        report = svc.validate(claim)
        assert report.completeness_score > 0.3

    def test_empty_claim_low_score(self, svc):
        report = svc.validate(ExtractedClaim())
        assert report.completeness_score < 0.2

    def test_score_between_0_and_1(self, svc):
        report = svc.validate(_make_claim())
        assert 0.0 <= report.completeness_score <= 1.0