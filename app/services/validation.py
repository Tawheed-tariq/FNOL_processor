"""
Validation Service

Applies domain rules to an ExtractedClaim and produces a ValidationReport.

Validation tiers:
  ERROR    required field is missing or value is logically impossible
  WARNING  field is present but suspicious (e.g. future date of loss)
  INFO     optional field absent (may affect routing but not validity)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import List, Tuple

from app.models.schemas import (
    ExtractedClaim,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)

logger = logging.getLogger(__name__)

# Fields considered "required" for a complete FNOL submission
REQUIRED_FIELDS: List[Tuple[str, str]] = [
    ("policy.policy_number",       "Policy number"),
    ("insured.name",               "Insured name"),
    ("incident.date_of_loss",      "Date of loss"),
    ("incident.description",       "Accident description"),
    ("vehicle.make",               "Vehicle make"),
    ("vehicle.model",              "Vehicle model"),
]

# Fields considered "important" (warning if missing)
IMPORTANT_FIELDS: List[Tuple[str, str]] = [
    ("policy.carrier",             "Carrier name"),
    ("insured.primary_phone",      "Insured primary phone"),
    ("incident.location_street",   "Location street"),
    ("vehicle.vin",                "VIN"),
    ("vehicle.damage_description", "Damage description"),
    ("driver.name",                "Driver name"),
]

# All tracked fields for completeness score
ALL_TRACKED_FIELDS: List[str] = [f for f, _ in REQUIRED_FIELDS + IMPORTANT_FIELDS] + [
    "policy.naic_code",
    "contact.name",
    "incident.report_number",
    "incident.time_of_loss",
    "vehicle.estimate_amount",
    "vehicle.year",
    "vehicle.plate_number",
    "driver.license_number",
    "owner.name",
]


class ValidationService:
    """
    Validates an ExtractedClaim and returns a ValidationReport.
    Stateless : safe to call concurrently.
    """

    def validate(self, claim: ExtractedClaim) -> ValidationReport:
        issues: List[ValidationIssue] = []
        missing_required: List[str] = []

        #  Required field presence
        for field_path, label in REQUIRED_FIELDS:
            val = self._get_field(claim, field_path)
            if not val:
                missing_required.append(field_path)
                issues.append(ValidationIssue(
                    field=field_path,
                    severity=ValidationSeverity.ERROR,
                    message=f"{label} is required but was not found in the document.",
                ))

        # Important field presence (warnings)
        for field_path, label in IMPORTANT_FIELDS:
            val = self._get_field(claim, field_path)
            if not val:
                issues.append(ValidationIssue(
                    field=field_path,
                    severity=ValidationSeverity.WARNING,
                    message=f"{label} is missing. This may delay claim processing.",
                ))

        # Date logic checks
        issues.extend(self._check_dates(claim))

        # VIN format check
        issues.extend(self._check_vin(claim))

        # Estimate sanity check
        issues.extend(self._check_estimate(claim))

        # Phone format check
        issues.extend(self._check_phone(claim))

        #  Child seat consistency
        issues.extend(self._check_child_seat(claim))

        # Compute completeness score
        filled = sum(
            1 for fp in ALL_TRACKED_FIELDS
            if self._get_field(claim, fp) not in (None, "", False)
        )
        score = round(filled / len(ALL_TRACKED_FIELDS), 3)

        is_valid = len(missing_required) == 0
        logger.info(
            "Validation complete: valid=%s, missing_required=%d, issues=%d, score=%.2f",
            is_valid, len(missing_required), len(issues), score,
        )

        return ValidationReport(
            is_valid=is_valid,
            missing_required_fields=missing_required,
            issues=issues,
            completeness_score=score,
        )

    # Field accessor
    def _get_field(self, claim: ExtractedClaim, dotted_path: str):
        """Navigate a dotted attribute path like 'policy.policy_number'."""
        parts = dotted_path.split(".")
        obj = claim
        for part in parts:
            if obj is None:
                return None
            obj = getattr(obj, part, None)
        return obj

    # Domain checks
    def _check_dates(self, claim: ExtractedClaim) -> List[ValidationIssue]:
        issues = []
        dol_raw = claim.incident.date_of_loss

        if dol_raw:
            parsed = self._try_parse_date(dol_raw)
            if parsed is None:
                issues.append(ValidationIssue(
                    field="incident.date_of_loss",
                    severity=ValidationSeverity.WARNING,
                    message=f"Date of loss '{dol_raw}' could not be parsed; verify format.",
                ))
            elif parsed > datetime.utcnow():
                issues.append(ValidationIssue(
                    field="incident.date_of_loss",
                    severity=ValidationSeverity.ERROR,
                    message=f"Date of loss '{dol_raw}' is in the future. Possible data entry error.",
                ))

        return issues

    def _check_vin(self, claim: ExtractedClaim) -> List[ValidationIssue]:
        issues = []
        vin = claim.vehicle.vin
        if vin:
            clean = vin.replace("-", "").replace(" ", "").upper()
            if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", clean):
                issues.append(ValidationIssue(
                    field="vehicle.vin",
                    severity=ValidationSeverity.WARNING,
                    message=f"VIN '{vin}' does not match the standard 17-character format.",
                ))
        return issues

    def _check_estimate(self, claim: ExtractedClaim) -> List[ValidationIssue]:
        issues = []
        est = claim.vehicle.estimate_amount
        if est is not None:
            if est < 0:
                issues.append(ValidationIssue(
                    field="vehicle.estimate_amount",
                    severity=ValidationSeverity.ERROR,
                    message="Damage estimate cannot be negative.",
                ))
            elif est > 500_000:
                issues.append(ValidationIssue(
                    field="vehicle.estimate_amount",
                    severity=ValidationSeverity.WARNING,
                    message=f"Damage estimate ${est:,.2f} is unusually high. Please verify.",
                ))
        return issues

    def _check_phone(self, claim: ExtractedClaim) -> List[ValidationIssue]:
        issues = []
        phone = claim.insured.primary_phone
        if phone:
            digits = re.sub(r"\D", "", phone)
            if len(digits) not in (10, 11):
                issues.append(ValidationIssue(
                    field="insured.primary_phone",
                    severity=ValidationSeverity.INFO,
                    message=f"Phone number '{phone}' may not be valid (expected 10–11 digits).",
                ))
        return issues

    def _check_child_seat(self, claim: ExtractedClaim) -> List[ValidationIssue]:
        issues = []
        cs = claim.child_seat
        # Logical check: if seat was not installed, it can't have been in use
        if cs.installed is False and cs.in_use_by_child is True:
            issues.append(ValidationIssue(
                field="child_seat.in_use_by_child",
                severity=ValidationSeverity.ERROR,
                message="Child seat marked 'in use' but 'installed' is No — logically inconsistent.",
            ))
        # If seat was not in use, it shouldn't have sustained damage from use
        if cs.in_use_by_child is False and cs.sustained_loss is True:
            issues.append(ValidationIssue(
                field="child_seat.sustained_loss",
                severity=ValidationSeverity.WARNING,
                message="Child seat sustained loss but was not in use at time of accident.",
            ))
        return issues

    # Utilities
    def _try_parse_date(self, raw: str) -> datetime | None:
        formats = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%y"]
        for fmt in formats:
            try:
                return datetime.strptime(raw.strip(), fmt)
            except ValueError:
                continue
        return None