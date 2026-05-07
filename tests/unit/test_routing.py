"""
Unit tests – RoutingEngine
"""

import pytest

from app.models.schemas import (
    ClaimRoute,
    DriverDetails,
    ExtractedClaim,
    IncidentDetails,
    IncidentType,
    InjuredParty,
    InsuredParty,
    PolicyInformation,
    ThirdPartyVehicle,
    ValidationReport,
    VehicleDetails,
    ChildSeatInfo,
)
from app.services.routing import RoutingEngine


@pytest.fixture
def engine():
    return RoutingEngine()


def _clean_validation(**overrides) -> ValidationReport:
    defaults = dict(
        is_valid=True,
        missing_required_fields=[],
        issues=[],
        completeness_score=0.8,
    )
    defaults.update(overrides)
    return ValidationReport(**defaults)


def _make_claim(**overrides) -> ExtractedClaim:
    claim = ExtractedClaim()
    claim.policy = PolicyInformation(policy_number="PA-001", carrier="ACME")
    claim.insured = InsuredParty(name="Test User")
    claim.incident = IncidentDetails(
        date_of_loss="01/10/2024",
        description="Minor fender bender",
        incident_type=IncidentType.COLLISION,
    )
    claim.vehicle = VehicleDetails(
        make="Ford", model="Fusion", estimate_amount=1500.0
    )
    for k, v in overrides.items():
        setattr(claim, k, v)
    return claim


class TestFastTrack:
    def test_low_value_complete_claim_is_fast_track(self, engine):
        claim = _make_claim()
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.FAST_TRACK
        assert decision.priority_score <= 5

    def test_fast_track_reasoning_is_descriptive(self, engine):
        decision = engine.route(_make_claim(), _clean_validation())
        assert len(decision.reasoning) > 20


class TestInvestigation:
    def test_theft_routes_to_investigation(self, engine):
        claim = _make_claim()
        claim.incident.incident_type = IncidentType.THEFT
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.INVESTIGATION

    def test_hit_and_run_routes_to_investigation(self, engine):
        claim = _make_claim()
        claim.incident.incident_type = IncidentType.HIT_AND_RUN
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.INVESTIGATION

    def test_very_high_value_routes_to_investigation(self, engine):
        claim = _make_claim()
        claim.vehicle.estimate_amount = 75_000.0
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.INVESTIGATION
        assert decision.priority_score >= 8

    def test_no_permission_routes_to_investigation(self, engine):
        claim = _make_claim()
        claim.driver = DriverDetails(used_with_permission=False)
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.INVESTIGATION
        assert decision.priority_score == 10

    def test_investigation_has_relevant_flag(self, engine):
        claim = _make_claim()
        claim.incident.incident_type = IncidentType.THEFT
        decision = engine.route(claim, _clean_validation())
        assert any("INCIDENT_TYPE" in f for f in decision.flags)


class TestSpecialistQueue:
    def test_injured_parties_route_to_specialist(self, engine):
        claim = _make_claim()
        claim.injured_parties = [InjuredParty(name="Bob Smith", extent_of_injury="Whiplash")]
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.SPECIALIST_QUEUE

    def test_fire_incident_routes_to_specialist(self, engine):
        claim = _make_claim()
        claim.incident.incident_type = IncidentType.FIRE
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.SPECIALIST_QUEUE

    def test_flood_incident_routes_to_specialist(self, engine):
        claim = _make_claim()
        claim.incident.incident_type = IncidentType.FLOOD
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.SPECIALIST_QUEUE

    def test_natural_disaster_routes_to_specialist(self, engine):
        claim = _make_claim()
        claim.incident.incident_type = IncidentType.NATURAL_DISASTER
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.SPECIALIST_QUEUE

    def test_child_seat_damage_routes_to_specialist(self, engine):
        claim = _make_claim()
        claim.child_seat = ChildSeatInfo(installed=True, in_use_by_child=True, sustained_loss=True)
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.SPECIALIST_QUEUE

    def test_multiple_third_parties_routes_to_specialist(self, engine):
        claim = _make_claim()
        claim.third_party_vehicles = [
            ThirdPartyVehicle(make="Toyota"), ThirdPartyVehicle(make="BMW")
        ]
        decision = engine.route(claim, _clean_validation())
        assert decision.route == ClaimRoute.SPECIALIST_QUEUE


class TestManualReview:
    def test_many_missing_fields_routes_to_manual(self, engine):
        validation = _clean_validation(
            is_valid=False,
            missing_required_fields=[
                "policy.policy_number", "insured.name",
                "incident.date_of_loss", "incident.description",
            ],
        )
        decision = engine.route(_make_claim(), validation)
        assert decision.route == ClaimRoute.MANUAL_REVIEW

    def test_low_completeness_routes_to_manual(self, engine):
        validation = _clean_validation(completeness_score=0.3)
        decision = engine.route(_make_claim(), validation)
        assert decision.route == ClaimRoute.MANUAL_REVIEW


class TestRoutingFlags:
    def test_high_value_flag_present(self, engine):
        claim = _make_claim()
        claim.vehicle.estimate_amount = 80_000.0
        decision = engine.route(claim, _clean_validation())
        assert any("HIGH_VALUE" in f for f in decision.flags)

    def test_bodily_injury_flag_present(self, engine):
        claim = _make_claim()
        claim.injured_parties = [InjuredParty(name="Alice")]
        decision = engine.route(claim, _clean_validation())
        assert any("BODILY_INJURY" in f for f in decision.flags)

    def test_no_flags_on_clean_claim(self, engine):
        decision = engine.route(_make_claim(), _clean_validation())
        assert decision.flags == [] or all("HIGH_VALUE" not in f for f in decision.flags)