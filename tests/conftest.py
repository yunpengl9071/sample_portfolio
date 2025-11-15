"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from trialsense.data.models import (
    ClinicalTrial,
    TrialPhase,
    TrialStatus,
    Sponsor,
    Condition,
    Intervention,
    Location,
)


@pytest.fixture
def sample_trial_data() -> dict:
    """Sample raw trial data from ClinicalTrials.gov API."""
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Test Trial for Cancer Treatment",
                "officialTitle": "A Phase 3 Study of Novel Cancer Treatment",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"year": 2023, "month": 1, "day": 15},
                "completionDateStruct": {"year": 2026, "month": 12, "day": 31},
                "primaryCompletionDateStruct": {"year": 2025, "month": 6, "day": 30},
                "enrollmentInfo": {"count": 300},
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {
                    "name": "Test Pharma Inc",
                    "class": "INDUSTRY",
                },
                "collaborators": [
                    {"name": "Academic Medical Center", "class": "OTHER"}
                ],
            },
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": ["PHASE3"],
                "designInfo": {
                    "allocation": "RANDOMIZED",
                    "interventionModel": "PARALLEL",
                    "primaryPurpose": "TREATMENT",
                    "maskingInfo": {"masking": "DOUBLE"},
                },
            },
            "conditionsModule": {
                "conditions": ["Lung Cancer", "Non-Small Cell Lung Cancer"],
                "keywords": ["immunotherapy", "checkpoint inhibitor"],
            },
            "armsInterventionsModule": {
                "interventions": [
                    {
                        "type": "DRUG",
                        "name": "Test Drug A",
                        "description": "Novel immunotherapy agent",
                    },
                    {
                        "type": "DRUG",
                        "name": "Placebo",
                        "description": "Control arm",
                    },
                ]
            },
            "eligibilityModule": {
                "eligibilityCriteria": "Inclusion: Age 18+, NSCLC diagnosis...",
                "minimumAge": "18 Years",
                "maximumAge": "85 Years",
                "sex": "ALL",
            },
            "contactsLocationsModule": {
                "locations": [
                    {
                        "facility": "Johns Hopkins Hospital",
                        "city": "Baltimore",
                        "state": "Maryland",
                        "country": "United States",
                        "zip": "21287",
                        "status": "RECRUITING",
                    }
                ]
            },
            "outcomesModule": {
                "primaryOutcomes": [
                    {"measure": "Overall Survival"}
                ],
                "secondaryOutcomes": [
                    {"measure": "Progression-Free Survival"},
                    {"measure": "Objective Response Rate"},
                ],
            },
            "descriptionModule": {
                "briefSummary": "This study evaluates a novel cancer treatment.",
                "detailedDescription": "Detailed description of the study...",
            },
        },
        "hasResults": False,
    }


@pytest.fixture
def sample_clinical_trial() -> ClinicalTrial:
    """Sample ClinicalTrial model instance."""
    return ClinicalTrial(
        nct_id="NCT12345678",
        title="A Phase 3 Study of Novel Cancer Treatment",
        status=TrialStatus.RECRUITING,
        phase=TrialPhase.PHASE_3,
        sponsor=Sponsor(name="Test Pharma Inc", type="INDUSTRY"),
        collaborators=[Sponsor(name="Academic Medical Center", type="OTHER")],
        study_type="INTERVENTIONAL",
        enrollment=300,
        allocation="RANDOMIZED",
        intervention_model="PARALLEL",
        primary_purpose="TREATMENT",
        masking="DOUBLE",
        conditions=[
            Condition(name="Lung Cancer"),
            Condition(name="Non-Small Cell Lung Cancer"),
        ],
        interventions=[
            Intervention(
                type="DRUG",
                name="Test Drug A",
                description="Novel immunotherapy agent",
            ),
            Intervention(type="DRUG", name="Placebo", description="Control arm"),
        ],
        eligibility_criteria="Inclusion: Age 18+, NSCLC diagnosis...",
        minimum_age="18 Years",
        maximum_age="85 Years",
        gender="ALL",
        start_date=datetime(2023, 1, 15).date(),
        completion_date=datetime(2026, 12, 31).date(),
        primary_completion_date=datetime(2025, 6, 30).date(),
        locations=[
            Location(
                facility="Johns Hopkins Hospital",
                city="Baltimore",
                state="Maryland",
                country="United States",
                zip_code="21287",
                status="RECRUITING",
            )
        ],
        primary_outcome="Overall Survival",
        secondary_outcomes=["Progression-Free Survival", "Objective Response Rate"],
        brief_summary="This study evaluates a novel cancer treatment.",
        detailed_description="Detailed description of the study...",
        keywords=["immunotherapy", "checkpoint inhibitor"],
        has_results=False,
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.aclose = AsyncMock()
    return client
