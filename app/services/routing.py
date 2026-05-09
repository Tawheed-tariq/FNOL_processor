"""
Routing Engine

Rule-based engine that determines the correct claim route based on
extracted data and validation results.

Routes (in priority order evaluated):
  1. Investigation       fraud indicators, hit-and-run, high value, unresolved inconsistencies
  2. Specialist Queue    injuries, fire/flood/natural disaster, child seat damage, >1 third party
  3. Manual Review       missing critical fields, inconsistencies, moderate complexity
  4. Fast-track          clean, low-value, simple collision with all data present
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from app.core.config import settings
from app.models.schemas import (
    ClaimRoute,
    ExtractedClaim,
    IncidentType,
    RoutingDecision,
    ValidationReport,
    ValidationSeverity,
)

logger = logging.getLogger(__name__)

# Incident types that trigger specialist routing
SPECIALIST_INCIDENT_TYPES = {
    IncidentType.FIRE,
    IncidentType.FLOOD,
    IncidentType.NATURAL_DISASTER,
}

# Incident types that may warrant investigation
INVESTIGATION_INCIDENT_TYPES = {
    IncidentType.THEFT,
    IncidentType.HIT_AND_RUN,
}


class RoutingEngine:
    """
    Stateless, rule-based routing engine.
    Returns a RoutingDecision with route, reasoning, priority, and flags.
    """

    def route(
        self,
        claim: ExtractedClaim,
        validation: ValidationReport,
    ) -> RoutingDecision:

        flags: List[str] = []
        reasons: List[str] = []

        # Gather signals
        estimate = claim.vehicle.estimate_amount
        incident_type = claim.incident.incident_type
        injured = claim.injured_parties
        child_seat_damage = (
            claim.child_seat.installed is True
            and claim.child_seat.sustained_loss is True
        )
        third_parties = claim.third_party_vehicles
        error_count = sum(1 for i in validation.issues if i.severity == ValidationSeverity.ERROR)
        missing_required = len(validation.missing_required_fields)
        police_report_missing = (
            claim.incident.police_contacted is True
            and not claim.incident.report_number
        )

        # Flag generation
        if estimate and estimate >= settings.INVESTIGATION_MIN_CLAIM_AMOUNT:
            flags.append(f"HIGH_VALUE_CLAIM: ${estimate:,.0f}")

        if incident_type in INVESTIGATION_INCIDENT_TYPES:
            flags.append(f"INCIDENT_TYPE: {incident_type.value}")

        if injured:
            flags.append(f"BODILY_INJURY: {len(injured)} party(ies) reported")

        if child_seat_damage:
            flags.append("CHILD_SEAT_DAMAGE")

        if len(third_parties) > 1:
            flags.append(f"MULTIPLE_THIRD_PARTIES: {len(third_parties)}")

        if missing_required > 0:
            flags.append(f"MISSING_REQUIRED_FIELDS: {missing_required}")

        if error_count > 0:
            flags.append(f"VALIDATION_ERRORS: {error_count}")

        if police_report_missing:
            flags.append("POLICE_CONTACTED_BUT_NO_REPORT_NUMBER")

        if claim.driver.used_with_permission is False:
            flags.append("VEHICLE_USED_WITHOUT_PERMISSION")

        completeness = validation.completeness_score

        # Routing rules (highest priority first)

        # 1. Investigation
        route, reasoning, priority = self._check_investigation(
            claim, flags, estimate, incident_type, error_count, missing_required, completeness
        )
        if route:
            return RoutingDecision(route=route, reasoning=reasoning, priority_score=priority, flags=flags)

        # 2. Specialist Queue
        route, reasoning, priority = self._check_specialist(
            claim, flags, injured, child_seat_damage, incident_type, third_parties
        )
        if route:
            return RoutingDecision(route=route, reasoning=reasoning, priority_score=priority, flags=flags)

        # 3. Manual Review
        route, reasoning, priority = self._check_manual_review(
            claim, flags, missing_required, error_count, completeness
        )
        if route:
            return RoutingDecision(route=route, reasoning=reasoning, priority_score=priority, flags=flags)

        # 4. Fast-track (default)
        return RoutingDecision(
            route=ClaimRoute.FAST_TRACK,
            reasoning=(
                "Claim meets all fast-track criteria: all required fields present, "
                f"no injuries reported, low-to-moderate damage estimate "
                f"({'$' + f'{estimate:,.0f}' if estimate else 'not specified'}), "
                f"data completeness score {completeness:.0%}. "
                "Eligible for automated processing."
            ),
            priority_score=3,
            flags=flags,
        )

    # rule evaluators
    def _check_investigation(
        self,
        claim: ExtractedClaim,
        flags: List[str],
        estimate: Optional[float],
        incident_type: IncidentType,
        error_count: int,
        missing_required: int,
        completeness: float,
    ) -> Tuple[Optional[ClaimRoute], str, int]:

        reasons = []
        priority = 8

        if incident_type in INVESTIGATION_INCIDENT_TYPES:
            reasons.append(
                f"incident type '{incident_type.value}' carries elevated fraud risk"
            )
            priority = max(priority, 9)

        if estimate and estimate >= settings.INVESTIGATION_MIN_CLAIM_AMOUNT:
            reasons.append(
                f"damage estimate ${estimate:,.0f} exceeds investigation threshold "
                f"${settings.INVESTIGATION_MIN_CLAIM_AMOUNT:,.0f}"
            )
            priority = max(priority, 9)

        if claim.driver.used_with_permission is False:
            reasons.append("vehicle was reportedly used without owner's permission")
            priority = 10

        if error_count >= 3 and completeness < 0.3:
            reasons.append(
                f"{error_count} validation errors with very low data completeness "
                f"({completeness:.0%}) — possible fraudulent/incomplete submission"
            )

        if reasons:
            return (
                ClaimRoute.INVESTIGATION,
                f"Routed to Investigation because: {'; '.join(reasons)}.",
                priority,
            )
        return None, "", 0

    def _check_specialist(
        self,
        claim: ExtractedClaim,
        flags: List[str],
        injured: list,
        child_seat_damage: bool,
        incident_type: IncidentType,
        third_parties: list,
    ) -> Tuple[Optional[ClaimRoute], str, int]:

        reasons = []
        priority = 7

        if injured:
            reasons.append(f"{len(injured)} injured party(ies) reported — requires medical liaison")
            priority = max(priority, 8)

        if incident_type in SPECIALIST_INCIDENT_TYPES:
            reasons.append(
                f"incident type '{incident_type.value}' requires specialised adjusting expertise"
            )

        if child_seat_damage:
            reasons.append(
                "child passenger restraint system sustained damage — "
                "requires specialist replacement evaluation"
            )

        if len(third_parties) > 1:
            reasons.append(
                f"{len(third_parties)} third-party vehicles involved — "
                "requires multi-party coordination specialist"
            )

        if reasons:
            return (
                ClaimRoute.SPECIALIST_QUEUE,
                f"Routed to Specialist Queue because: {'; '.join(reasons)}.",
                priority,
            )
        return None, "", 0

    def _check_manual_review(
        self,
        claim: ExtractedClaim,
        flags: List[str],
        missing_required: int,
        error_count: int,
        completeness: float,
    ) -> Tuple[Optional[ClaimRoute], str, int]:

        reasons = []
        priority = 5

        if missing_required >= settings.MISSING_FIELDS_MANUAL_THRESHOLD:
            reasons.append(
                f"{missing_required} required fields are absent — "
                "cannot process automatically without outreach to insured"
            )
            priority = max(priority, 6)

        if error_count > 0:
            reasons.append(
                f"{error_count} validation error(s) require human review "
                "(e.g. inconsistent dates, invalid VIN)"
            )

        if completeness < 0.45:
            reasons.append(
                f"data completeness score is {completeness:.0%}, "
                "below the minimum threshold for automated processing"
            )

        if reasons:
            return (
                ClaimRoute.MANUAL_REVIEW,
                f"Routed to Manual Review because: {'; '.join(reasons)}.",
                priority,
            )
        return None, "", 0