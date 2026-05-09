from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# Enumerations

class ClaimRoute(str, Enum):
    FAST_TRACK = "Fast-track"
    MANUAL_REVIEW = "Manual Review"
    INVESTIGATION = "Investigation"
    SPECIALIST_QUEUE = "Specialist Queue"


class IncidentType(str, Enum):
    COLLISION = "Collision"
    THEFT = "Theft"
    VANDALISM = "Vandalism"
    NATURAL_DISASTER = "Natural Disaster"
    FIRE = "Fire"
    FLOOD = "Flood"
    HIT_AND_RUN = "Hit and Run"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Sub-models

class PolicyInformation(BaseModel):
    policy_number: Optional[str] = Field(None, description="Insurance policy number")
    carrier: Optional[str] = Field(None, description="Insurance carrier / company name")
    naic_code: Optional[str] = Field(None, description="NAIC code of the carrier")
    line_of_business: Optional[str] = Field(None, description="Line of business, e.g. Auto")
    insured_location_code: Optional[str] = Field(None, description="Insured location code")
    agency_name: Optional[str] = Field(None, description="Agency name")
    agency_code: Optional[str] = Field(None, description="Agency code")


class InsuredParty(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the insured")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (MM/DD/YYYY)")
    mailing_address: Optional[str] = Field(None, description="Mailing address")
    primary_phone: Optional[str] = Field(None, description="Primary contact phone")
    email: Optional[str] = Field(None, description="Primary email address")


class ContactParty(BaseModel):
    name: Optional[str] = Field(None, description="Contact person name")
    mailing_address: Optional[str] = Field(None, description="Contact mailing address")
    primary_phone: Optional[str] = Field(None, description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    when_to_contact: Optional[str] = Field(None, description="Preferred contact time")


class IncidentDetails(BaseModel):
    date_of_loss: Optional[str] = Field(None, description="Date of the loss event (MM/DD/YYYY)")
    time_of_loss: Optional[str] = Field(None, description="Time of the loss event")
    location_street: Optional[str] = Field(None, description="Street address of incident")
    location_city_state_zip: Optional[str] = Field(None, description="City, state, ZIP of incident")
    location_country: Optional[str] = Field(None, description="Country of incident")
    police_contacted: Optional[bool] = Field(None, description="Whether police/fire was contacted")
    report_number: Optional[str] = Field(None, description="Police/fire report number")
    description: Optional[str] = Field(None, description="Free-text description of the accident")
    incident_type: IncidentType = Field(IncidentType.UNKNOWN, description="Classified incident type")


class VehicleDetails(BaseModel):
    veh_number: Optional[str] = Field(None, description="Vehicle number in policy")
    year: Optional[str] = Field(None, description="Vehicle year")
    make: Optional[str] = Field(None, description="Vehicle make")
    model: Optional[str] = Field(None, description="Vehicle model")
    body_type: Optional[str] = Field(None, description="Vehicle body type")
    vin: Optional[str] = Field(None, description="Vehicle Identification Number")
    plate_number: Optional[str] = Field(None, description="License plate number")
    plate_state: Optional[str] = Field(None, description="License plate state")
    damage_description: Optional[str] = Field(None, description="Description of damage")
    estimate_amount: Optional[float] = Field(None, description="Estimated damage amount in USD")
    where_can_be_seen: Optional[str] = Field(None, description="Where vehicle can be inspected")
    when_can_be_seen: Optional[str] = Field(None, description="When vehicle can be inspected")
    other_insurance_carrier: Optional[str] = Field(None, description="Other insurance on vehicle")
    other_insurance_policy: Optional[str] = Field(None, description="Other policy number")


class OwnerDetails(BaseModel):
    name: Optional[str] = Field(None, description="Owner name")
    address: Optional[str] = Field(None, description="Owner address")
    primary_phone: Optional[str] = Field(None, description="Owner phone")
    email: Optional[str] = Field(None, description="Owner email")
    same_as_insured: bool = Field(False, description="Owner is same as insured")


class DriverDetails(BaseModel):
    name: Optional[str] = Field(None, description="Driver name")
    address: Optional[str] = Field(None, description="Driver address")
    primary_phone: Optional[str] = Field(None, description="Driver phone")
    email: Optional[str] = Field(None, description="Driver email")
    date_of_birth: Optional[str] = Field(None, description="Driver date of birth")
    license_number: Optional[str] = Field(None, description="Driver license number")
    license_state: Optional[str] = Field(None, description="License issuing state")
    relation_to_insured: Optional[str] = Field(None, description="Driver's relation to insured")
    purpose_of_use: Optional[str] = Field(None, description="Purpose of use of vehicle")
    used_with_permission: Optional[bool] = Field(None, description="Was vehicle used with permission?")
    same_as_owner: bool = Field(False, description="Driver is same as owner")


class ChildSeatInfo(BaseModel):
    installed: Optional[bool] = Field(None, description="Was child seat installed?")
    in_use_by_child: Optional[bool] = Field(None, description="Was child seat in use?")
    sustained_loss: Optional[bool] = Field(None, description="Did child seat sustain damage?")


class ThirdPartyVehicle(BaseModel):
    veh_number: Optional[str] = None
    year: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    vin: Optional[str] = None
    plate_number: Optional[str] = None
    plate_state: Optional[str] = None
    owner_name: Optional[str] = None
    owner_address: Optional[str] = None
    owner_phone: Optional[str] = None
    driver_name: Optional[str] = None
    driver_address: Optional[str] = None
    driver_phone: Optional[str] = None
    damage_description: Optional[str] = None
    estimate_amount: Optional[float] = None
    carrier_name: Optional[str] = None
    policy_number: Optional[str] = None
    has_other_vehicle_insurance: Optional[bool] = None


class InjuredParty(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    vehicle_number: Optional[str] = None
    age: Optional[str] = None
    extent_of_injury: Optional[str] = None
    is_pedestrian: bool = False
    other_vehicle_insurance: Optional[str] = None


class Witness(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_passenger: bool = False
    vehicle_number: Optional[str] = None


# Validation models─

class ValidationIssue(BaseModel):
    field: str
    severity: ValidationSeverity
    message: str


class ValidationReport(BaseModel):
    is_valid: bool
    missing_required_fields: List[str] = Field(default_factory=list)
    issues: List[ValidationIssue] = Field(default_factory=list)
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="0.0–1.0 data completeness ratio"
    )


# Routing─

class RoutingDecision(BaseModel):
    route: ClaimRoute
    reasoning: str = Field(..., description="Human-readable explanation of routing decision")
    priority_score: int = Field(
        ..., ge=1, le=10, description="Priority score 1 (low) – 10 (urgent)"
    )
    flags: List[str] = Field(default_factory=list, description="Notable flags affecting routing")


# Extracted claim─

class ExtractedClaim(BaseModel):
    """Full structured representation of a processed FNOL document."""

    policy: PolicyInformation = Field(default_factory=PolicyInformation)
    insured: InsuredParty = Field(default_factory=InsuredParty)
    contact: ContactParty = Field(default_factory=ContactParty)
    incident: IncidentDetails = Field(default_factory=IncidentDetails)
    vehicle: VehicleDetails = Field(default_factory=VehicleDetails)
    owner: OwnerDetails = Field(default_factory=OwnerDetails)
    driver: DriverDetails = Field(default_factory=DriverDetails)
    child_seat: ChildSeatInfo = Field(default_factory=ChildSeatInfo)
    third_party_vehicles: List[ThirdPartyVehicle] = Field(default_factory=list)
    injured_parties: List[InjuredParty] = Field(default_factory=list)
    witnesses: List[Witness] = Field(default_factory=list)
    remarks: Optional[str] = None

    raw_llm_output: Optional[str] = Field(
        None, description="Raw LLM JSON string for debugging"
    )


# API request / response models─

class ProcessingMetadata(BaseModel):
    filename: str
    file_size_bytes: int
    pages_extracted: int
    characters_extracted: int
    processing_time_ms: float
    llm_model: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class ClaimProcessingResponse(BaseModel):
    claim_id: str = Field(..., description="Unique identifier for this processing run")
    status: str = Field(..., description="'success' or 'partial'")
    extracted_claim: ExtractedClaim
    validation: ValidationReport
    routing: RoutingDecision
    metadata: ProcessingMetadata


class BatchProcessingItem(BaseModel):
    filename: str
    claim_id: Optional[str] = None
    status: str            # success | partial | error
    response: Optional[ClaimProcessingResponse] = None
    error: Optional[str] = None


class BatchProcessingResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    items: List[BatchProcessingItem]
    batch_processing_time_ms: float


class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None
    field: Optional[str] = None