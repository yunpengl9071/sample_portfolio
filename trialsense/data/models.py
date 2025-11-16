"""Data models for clinical trials."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TrialPhase(str, Enum):
    """Clinical trial phases."""

    EARLY_PHASE_1 = "EARLY_PHASE1"
    PHASE_1 = "PHASE1"
    PHASE_2 = "PHASE2"
    PHASE_3 = "PHASE3"
    PHASE_4 = "PHASE4"
    NOT_APPLICABLE = "NA"


class TrialStatus(str, Enum):
    """Clinical trial recruitment status."""

    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    RECRUITING = "RECRUITING"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN = "UNKNOWN"


class Sponsor(BaseModel):
    """Trial sponsor information."""

    name: str
    type: Optional[str] = None  # INDUSTRY, NIH, FED, OTHER


class Condition(BaseModel):
    """Medical condition being studied."""

    name: str
    mesh_term: Optional[str] = None


class Intervention(BaseModel):
    """Trial intervention/treatment."""

    type: str  # Drug, Device, Procedure, etc.
    name: str
    description: Optional[str] = None


class Location(BaseModel):
    """Trial site location."""

    facility: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    zip_code: Optional[str] = None
    status: Optional[str] = None


class ClinicalTrial(BaseModel):
    """Clinical trial data model."""

    nct_id: str = Field(..., description="NCT identifier")
    title: str
    status: TrialStatus
    phase: Optional[TrialPhase] = None

    # Sponsorship
    sponsor: Sponsor
    collaborators: list[Sponsor] = Field(default_factory=list)

    # Study design
    study_type: str
    enrollment: Optional[int] = None
    allocation: Optional[str] = None
    intervention_model: Optional[str] = None
    primary_purpose: Optional[str] = None
    masking: Optional[str] = None

    # Medical details
    conditions: list[Condition] = Field(default_factory=list)
    interventions: list[Intervention] = Field(default_factory=list)

    # Eligibility
    eligibility_criteria: Optional[str] = None
    minimum_age: Optional[str] = None
    maximum_age: Optional[str] = None
    gender: Optional[str] = None

    # Dates
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    primary_completion_date: Optional[date] = None

    # Locations
    locations: list[Location] = Field(default_factory=list)

    # Outcomes
    primary_outcome: Optional[str] = None
    secondary_outcomes: list[str] = Field(default_factory=list)

    # Additional metadata
    brief_summary: Optional[str] = None
    detailed_description: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)

    # Termination information
    why_stopped: Optional[str] = None  # Reason for early termination

    # Calculated fields
    has_results: bool = False

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            date: lambda v: v.isoformat() if v else None,
        },
    )
