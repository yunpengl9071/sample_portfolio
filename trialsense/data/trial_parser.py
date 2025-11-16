"""Parser for uploaded trial protocols.

Handles parsing of trial data from various formats:
- JSON uploads
- Form data (from Streamlit)
- Future: PDF protocol parsing
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path

from trialsense.data.models import ClinicalTrial, TrialPhase, TrialStatus, Sponsor, Condition, Intervention, Location
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class TrialParser:
    """
    Parser for trial protocol uploads.

    Converts uploaded data (JSON, form) into structured format
    that can be used for feature extraction.
    """

    def parse_json(self, json_data: str | Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON trial protocol.

        Args:
            json_data: JSON string or dict containing trial data

        Returns:
            Standardized trial data dictionary

        Example JSON structure:
            {
                "title": "Phase 3 Study of Novel Drug",
                "phase": "PHASE_3",
                "enrollment": 340,
                "sponsor": {"name": "Acme Pharma", "type": "INDUSTRY"},
                "study_type": "INTERVENTIONAL",
                "allocation": "RANDOMIZED",
                "masking": "DOUBLE",
                "interventions": [...],
                "conditions": [...],
                ...
            }
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        # Standardize field names and types
        parsed = {
            "title": data.get("title", ""),
            "phase": data.get("phase"),
            "enrollment": data.get("enrollment"),
            "study_type": data.get("study_type", "INTERVENTIONAL"),
            "allocation": data.get("allocation"),
            "masking": data.get("masking"),
            "sponsor": data.get("sponsor", {}),
            "collaborators": data.get("collaborators", []),
            "conditions": data.get("conditions", []),
            "interventions": data.get("interventions", []),
            "locations": data.get("locations", []),
            "primary_outcome": data.get("primary_outcome", {}),
            "secondary_outcomes": data.get("secondary_outcomes", []),
            "eligibility_criteria": data.get("eligibility_criteria", ""),
            "minimum_age": data.get("minimum_age"),
            "maximum_age": data.get("maximum_age"),
            "brief_summary": data.get("brief_summary", ""),
        }

        logger.info(f"Parsed JSON protocol: {parsed.get('title', 'Untitled')}")
        return parsed

    def parse_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse form data from Streamlit UI.

        Args:
            form_data: Dictionary of form field values

        Returns:
            Standardized trial data dictionary
        """
        # Convert form fields to standard format
        parsed = {
            "title": form_data.get("title", ""),
            "phase": self._normalize_phase(form_data.get("phase")),
            "enrollment": form_data.get("enrollment"),
            "study_type": form_data.get("study_type", "INTERVENTIONAL"),
            "allocation": "RANDOMIZED" if form_data.get("is_randomized") else "NON_RANDOMIZED",
            "masking": self._normalize_masking(form_data.get("masking", "NONE")),
            "sponsor": {
                "name": form_data.get("sponsor_name", ""),
                "type": form_data.get("sponsor_type", "INDUSTRY"),
            },
            "collaborators": self._parse_collaborators(form_data.get("collaborators", "")),
            "conditions": [
                {"name": cond.strip()}
                for cond in form_data.get("conditions", "").split(",")
                if cond.strip()
            ],
            "interventions": self._parse_interventions(form_data.get("interventions", [])),
            "locations": self._parse_locations(form_data.get("locations", [])),
            "primary_outcome": {
                "measure": form_data.get("primary_outcome_measure", ""),
                "time_frame": form_data.get("primary_outcome_timeframe", ""),
            },
            "secondary_outcomes": [],
            "eligibility_criteria": form_data.get("eligibility_criteria", ""),
            "minimum_age": form_data.get("minimum_age"),
            "maximum_age": form_data.get("maximum_age"),
            "brief_summary": form_data.get("brief_summary", ""),
        }

        # Add secondary outcomes count
        num_secondary = form_data.get("num_secondary_outcomes", 0)
        parsed["secondary_outcomes"] = [
            {"measure": f"Secondary outcome {i+1}", "time_frame": ""}
            for i in range(num_secondary)
        ]

        logger.info(f"Parsed form data: {parsed.get('title', 'Untitled')}")
        return parsed

    def create_trial_object(self, parsed_data: Dict[str, Any]) -> ClinicalTrial:
        """
        Create a ClinicalTrial object from parsed data.

        Args:
            parsed_data: Standardized trial data dictionary

        Returns:
            ClinicalTrial object (may be partial/incomplete)
        """
        # Create sponsor
        sponsor_data = parsed_data.get("sponsor", {})
        sponsor = Sponsor(
            name=sponsor_data.get("name", "Unknown"),
            type=sponsor_data.get("type", "UNKNOWN"),
        )

        # Create conditions
        conditions = []
        for cond_data in parsed_data.get("conditions", []):
            conditions.append(Condition(name=cond_data.get("name", "Unknown")))

        # Create interventions
        interventions = []
        for int_data in parsed_data.get("interventions", []):
            interventions.append(
                Intervention(
                    type=int_data.get("type", "DRUG"),
                    name=int_data.get("name", ""),
                    description=int_data.get("description", ""),
                )
            )

        # Create locations
        locations = []
        for loc_data in parsed_data.get("locations", []):
            locations.append(
                Location(
                    facility=loc_data.get("facility", ""),
                    city=loc_data.get("city", ""),
                    state=loc_data.get("state", ""),
                    country=loc_data.get("country", ""),
                )
            )

        # Parse phase
        phase_str = parsed_data.get("phase")
        if isinstance(phase_str, str):
            try:
                phase = TrialPhase[phase_str.upper().replace(" ", "_")]
            except KeyError:
                phase = None
        else:
            phase = phase_str

        # Create trial object
        trial = ClinicalTrial(
            nct_id="NEW_TRIAL",  # Placeholder for new trials
            title=parsed_data.get("title", "Untitled Trial"),
            brief_summary=parsed_data.get("brief_summary", ""),
            status=TrialStatus.NOT_YET_RECRUITING,  # Default for new trials
            phase=phase,
            study_type=parsed_data.get("study_type", "INTERVENTIONAL"),
            allocation=parsed_data.get("allocation"),
            masking=parsed_data.get("masking"),
            enrollment=parsed_data.get("enrollment"),
            sponsor=sponsor,
            collaborators=[],  # Simplified
            conditions=conditions,
            interventions=interventions,
            locations=locations,
            eligibility_criteria=parsed_data.get("eligibility_criteria", ""),
            minimum_age=parsed_data.get("minimum_age"),
            maximum_age=parsed_data.get("maximum_age"),
            primary_outcome=parsed_data.get("primary_outcome", {}),
            secondary_outcomes=parsed_data.get("secondary_outcomes", []),
        )

        logger.info(f"Created ClinicalTrial object for: {trial.title}")
        return trial

    def _normalize_phase(self, phase_input: Optional[str]) -> Optional[str]:
        """Normalize phase string to standard format."""
        if not phase_input:
            return None

        phase_map = {
            "Early Phase 1": "EARLY_PHASE_1",
            "Phase 1": "PHASE_1",
            "Phase 2": "PHASE_2",
            "Phase 3": "PHASE_3",
            "Phase 4": "PHASE_4",
            "early phase 1": "EARLY_PHASE_1",
            "phase 1": "PHASE_1",
            "phase 2": "PHASE_2",
            "phase 3": "PHASE_3",
            "phase 4": "PHASE_4",
        }

        return phase_map.get(phase_input, phase_input.upper().replace(" ", "_"))

    def _normalize_masking(self, masking_input: str) -> str:
        """Normalize masking/blinding string."""
        masking_map = {
            "None": "NONE",
            "Single": "SINGLE",
            "Double": "DOUBLE",
            "Triple": "TRIPLE",
            "Quadruple": "QUADRUPLE",
            "none": "NONE",
            "single": "SINGLE",
            "double": "DOUBLE",
            "triple": "TRIPLE",
        }

        return masking_map.get(masking_input, masking_input.upper())

    def _parse_collaborators(self, collaborators_input: str) -> list:
        """Parse comma-separated collaborators string."""
        if not collaborators_input:
            return []

        collaborators = []
        for collab_name in collaborators_input.split(","):
            collab_name = collab_name.strip()
            if collab_name:
                collaborators.append({"name": collab_name})

        return collaborators

    def _parse_interventions(self, interventions_input: Any) -> list:
        """Parse interventions from various input formats."""
        if isinstance(interventions_input, list):
            return interventions_input
        elif isinstance(interventions_input, str):
            # Parse simple format: "Drug A, Drug B"
            interventions = []
            for int_name in interventions_input.split(","):
                int_name = int_name.strip()
                if int_name:
                    interventions.append({
                        "type": "DRUG",
                        "name": int_name,
                        "description": "",
                    })
            return interventions
        else:
            return []

    def _parse_locations(self, locations_input: Any) -> list:
        """Parse locations from various input formats."""
        if isinstance(locations_input, list):
            return locations_input
        elif isinstance(locations_input, str):
            # Parse simple format: "City, State"
            locations = []
            for loc_str in locations_input.split(";"):
                loc_str = loc_str.strip()
                if loc_str:
                    parts = [p.strip() for p in loc_str.split(",")]
                    locations.append({
                        "facility": parts[0] if len(parts) > 0 else "",
                        "city": parts[1] if len(parts) > 1 else "",
                        "state": parts[2] if len(parts) > 2 else "",
                        "country": parts[3] if len(parts) > 3 else "USA",
                    })
            return locations
        else:
            return []

    def validate_upload(self, parsed_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate that uploaded data has minimum required fields.

        Args:
            parsed_data: Parsed trial data

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not parsed_data.get("title"):
            errors.append("Trial title is required")

        if not parsed_data.get("phase"):
            errors.append("Trial phase is required")

        if not parsed_data.get("enrollment") or parsed_data["enrollment"] <= 0:
            errors.append("Valid enrollment number is required")

        if not parsed_data.get("conditions"):
            errors.append("At least one condition is required")

        is_valid = len(errors) == 0
        return is_valid, errors


# Convenience function
def parse_trial_upload(
    upload_data: str | Dict[str, Any], upload_type: str = "json"
) -> Dict[str, Any]:
    """
    Parse trial upload and return standardized data.

    Args:
        upload_data: JSON string, dict, or form data
        upload_type: "json" or "form"

    Returns:
        Standardized trial data dictionary
    """
    parser = TrialParser()

    if upload_type == "json":
        return parser.parse_json(upload_data)
    elif upload_type == "form":
        return parser.parse_form(upload_data)
    else:
        raise ValueError(f"Unknown upload type: {upload_type}")
