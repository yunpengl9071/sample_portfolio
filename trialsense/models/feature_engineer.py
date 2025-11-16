"""Feature engineering module for clinical trial outcome prediction.

This module handles:
1. Extracting features from complete ClinicalTrial objects (existing trials)
2. Extracting features from partial data (new trial uploads)
3. Validating feature completeness
4. Generating prompts for missing required features
5. Loading/saving feature schemas
"""

from typing import Optional, Any, Dict, List, Union
from pathlib import Path
from dataclasses import dataclass, field
import json
import numpy as np

from trialsense.data.models import ClinicalTrial, TrialPhase
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FeatureDefinition:
    """Definition of a single feature."""

    name: str
    type: str  # "numeric", "categorical_encoded", "boolean"
    required: bool
    encoding: Optional[Dict[str, int]] = None
    default: Optional[Union[int, float, str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    importance: Optional[float] = None
    description: str = ""


@dataclass
class FeatureSchema:
    """Schema defining all features used by the model."""

    version: str
    model_type: str
    trained_on: str
    n_trials: int
    features: List[FeatureDefinition]
    feature_order: List[str]


# Feature prompts for interactive UI
FEATURE_PROMPTS = {
    "phase_numeric": {
        "question": "What is the trial phase?",
        "type": "select",
        "options": ["Early Phase 1", "Phase 1", "Phase 2", "Phase 3", "Phase 4"],
        "required": True,
        "help": "The clinical trial phase determines the stage of drug development and affects success probability.",
    },
    "enrollment": {
        "question": "What is the target enrollment (number of participants)?",
        "type": "number",
        "min": 1,
        "max": 100000,
        "required": True,
        "help": "Total number of participants you plan to enroll across all sites. Larger trials are more expensive but provide stronger evidence.",
    },
    "sponsor_type": {
        "question": "What type of organization is sponsoring this trial?",
        "type": "select",
        "options": ["Industry", "Academic", "Government", "Other"],
        "required": True,
        "help": "Industry sponsors tend to have more resources but face different regulatory scrutiny.",
    },
    "is_randomized": {
        "question": "Is this a randomized trial?",
        "type": "boolean",
        "default": True,
        "required": True,
        "help": "Randomization improves evidence quality and regulatory approval likelihood.",
    },
    "is_blinded": {
        "question": "Is this trial blinded/masked?",
        "type": "select",
        "options": ["None", "Single", "Double", "Triple"],
        "required": True,
        "help": "Blinding reduces bias. Double-blind is standard for drug trials.",
    },
    "is_interventional": {
        "question": "Is this an interventional study?",
        "type": "boolean",
        "default": True,
        "required": False,
        "help": "Most drug trials are interventional (vs observational).",
    },
    "num_interventions": {
        "question": "How many intervention arms does this trial have?",
        "type": "number",
        "min": 1,
        "max": 10,
        "required": True,
        "help": "Including all treatment arms and control/placebo arms.",
    },
    "num_locations": {
        "question": "How many trial sites/locations are planned?",
        "type": "number",
        "min": 1,
        "max": 1000,
        "required": False,
        "default": None,
        "help": (
            "Number of trial sites/locations. If uncertain during design phase, "
            "we can estimate based on enrollment target:\n"
            "  • <50 participants: typically 1-3 sites\n"
            "  • 50-200 participants: typically 5-15 sites\n"
            "  • 200-500 participants: typically 15-40 sites\n"
            "  • >500 participants: typically 40+ sites\n"
            "Multi-site trials have higher recruitment but increase coordination complexity."
        ),
    },
    "num_conditions": {
        "question": "How many conditions/diseases are being studied?",
        "type": "number",
        "min": 1,
        "max": 10,
        "default": 1,
        "required": False,
        "help": "Most trials focus on a single primary condition.",
    },
    "num_secondary_outcomes": {
        "question": "How many secondary outcome measures?",
        "type": "number",
        "min": 0,
        "max": 20,
        "default": 2,
        "required": False,
        "help": "Secondary outcomes provide additional evidence but increase trial complexity.",
    },
    "has_age_restriction": {
        "question": "Are there age restrictions?",
        "type": "boolean",
        "default": True,
        "required": False,
        "help": "Most trials have minimum/maximum age requirements.",
    },
    "has_collaborators": {
        "question": "Are there collaborating organizations?",
        "type": "boolean",
        "default": False,
        "required": False,
        "help": "Collaborators can provide expertise and resources.",
    },
    "therapeutic_area": {
        "question": "Primary therapeutic area?",
        "type": "text",
        "required": True,
        "help": "e.g., 'Oncology', 'Cardiovascular', 'Neurology'",
    },
    "has_adaptive_design": {
        "question": "Does this trial use an adaptive design?",
        "type": "boolean",
        "default": False,
        "required": False,
        "help": (
            "Adaptive trials can modify aspects like sample size, "
            "treatment arms, or eligibility during the trial based on interim results. "
            "Examples: basket trials, umbrella trials, platform trials."
        ),
    },
    "biomarker_driven": {
        "question": "Is this a biomarker-driven trial?",
        "type": "boolean",
        "default": False,
        "required": False,
        "help": (
            "Biomarker-driven trials use companion diagnostics or genomic markers "
            "to stratify patients or guide treatment selection. "
            "More common in oncology and precision medicine."
        ),
    },
    "has_patient_reported_outcomes": {
        "question": "Does the trial include patient-reported outcomes (PROs)?",
        "type": "boolean",
        "default": False,
        "required": False,
        "help": (
            "PROs measure quality of life, symptoms, or functional status "
            "as reported by patients. Increasingly important for FDA approvals."
        ),
    },
}


class FeatureEngineer:
    """
    Feature engineering for clinical trial outcome prediction.

    Handles feature extraction from complete or partial trial data,
    validates completeness, and generates prompts for missing features.
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize feature engineer.

        Args:
            schema_path: Path to feature schema JSON (optional)
        """
        self.schema: Optional[FeatureSchema] = None
        self.required_features: List[str] = []

        if schema_path and Path(schema_path).exists():
            self.load_schema(schema_path)
        else:
            # Use default feature set
            self._initialize_default_features()

    def _initialize_default_features(self) -> None:
        """Initialize with default feature set."""
        self.required_features = [
            "phase_numeric",
            "enrollment",
            "enrollment_log",
            "sponsor_type",
            "is_randomized",
            "is_blinded",
            "num_interventions",
            # num_locations is optional - can be estimated from enrollment
            "therapeutic_area",
        ]
        logger.info("Initialized with default feature set")

    def extract_features(
        self, trial: ClinicalTrial, user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract features from a complete ClinicalTrial object.

        This is used for existing trials fetched from ClinicalTrials.gov.

        Args:
            trial: ClinicalTrial object
            user_inputs: Optional user-provided values to override/fill missing

        Returns:
            Dictionary of feature name -> value
        """
        features = {}

        # Phase features
        features["phase_numeric"] = self._encode_phase(trial.phase)

        # Enrollment features
        features["enrollment"] = trial.enrollment or 0
        features["enrollment_log"] = (
            np.log1p(trial.enrollment) if trial.enrollment else 0
        )

        # Sponsor features
        features["sponsor_type"] = trial.sponsor.type if trial.sponsor else "UNKNOWN"
        features["has_collaborators"] = 1 if len(trial.collaborators) > 0 else 0
        features["num_collaborators"] = len(trial.collaborators)

        # Study design features
        features["is_randomized"] = 1 if trial.allocation == "RANDOMIZED" else 0
        features["is_blinded"] = (
            1 if trial.masking and trial.masking != "NONE" else 0
        )
        features["is_interventional"] = (
            1 if trial.study_type == "INTERVENTIONAL" else 0
        )

        # Complexity features
        features["num_conditions"] = len(trial.conditions)
        features["num_interventions"] = len(trial.interventions)
        features["num_locations"] = len(trial.locations)
        features["num_secondary_outcomes"] = len(trial.secondary_outcomes)

        # Eligibility features
        features["has_age_restriction"] = (
            1 if trial.minimum_age or trial.maximum_age else 0
        )
        features["criteria_length"] = (
            len(trial.eligibility_criteria) if trial.eligibility_criteria else 0
        )

        # Site features
        features["is_multicenter"] = 1 if len(trial.locations) > 1 else 0

        # Therapeutic area
        features["therapeutic_area"] = (
            trial.conditions[0].name if trial.conditions else "Unknown"
        )

        # Advanced trial design features
        features["has_adaptive_design"] = self._detect_adaptive_design(trial)
        features["biomarker_driven"] = self._detect_biomarker_driven(trial)
        features["has_patient_reported_outcomes"] = self._detect_pro(trial)

        # Override with user inputs if provided
        if user_inputs:
            features.update(user_inputs)

        return features

    def extract_features_partial(
        self, trial_data: Dict[str, Any], user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract features from partial trial data (e.g., uploaded JSON/form).

        This is used for new trials being designed where data is incomplete.

        Args:
            trial_data: Partial trial data dictionary
            user_inputs: User-provided values for missing features

        Returns:
            Dictionary of feature name -> value (may be incomplete)
        """
        features = {}

        # Phase
        phase_str = trial_data.get("phase")
        if phase_str:
            phase_enum = self._parse_phase(phase_str)
            features["phase_numeric"] = self._encode_phase(phase_enum)
        else:
            features["phase_numeric"] = None

        # Enrollment
        enrollment = trial_data.get("enrollment")
        features["enrollment"] = enrollment
        features["enrollment_log"] = np.log1p(enrollment) if enrollment else None

        # Sponsor
        sponsor = trial_data.get("sponsor", {})
        features["sponsor_type"] = sponsor.get("type", None)
        collaborators = trial_data.get("collaborators", [])
        features["has_collaborators"] = 1 if collaborators else 0
        features["num_collaborators"] = len(collaborators) if collaborators else 0

        # Design
        allocation = trial_data.get("allocation")
        features["is_randomized"] = 1 if allocation == "RANDOMIZED" else 0

        masking = trial_data.get("masking")
        features["is_blinded"] = 1 if masking and masking != "NONE" else 0

        study_type = trial_data.get("study_type")
        features["is_interventional"] = 1 if study_type == "INTERVENTIONAL" else 1  # default to 1

        # Complexity
        conditions = trial_data.get("conditions", [])
        features["num_conditions"] = len(conditions) if conditions else 1

        interventions = trial_data.get("interventions", [])
        features["num_interventions"] = len(interventions) if interventions else None

        locations = trial_data.get("locations", [])
        features["num_locations"] = len(locations) if locations else None

        secondary_outcomes = trial_data.get("secondary_outcomes", [])
        features["num_secondary_outcomes"] = len(secondary_outcomes) if secondary_outcomes else 2

        # Eligibility
        has_min_age = trial_data.get("minimum_age") is not None
        has_max_age = trial_data.get("maximum_age") is not None
        features["has_age_restriction"] = 1 if has_min_age or has_max_age else 0

        criteria = trial_data.get("eligibility_criteria", "")
        features["criteria_length"] = len(criteria) if criteria else 0

        # Sites
        features["is_multicenter"] = 1 if features["num_locations"] and features["num_locations"] > 1 else 0

        # Therapeutic area
        if conditions:
            features["therapeutic_area"] = conditions[0].get("name", None)
        else:
            features["therapeutic_area"] = None

        # Advanced trial design features (default to 0 for partial data)
        features["has_adaptive_design"] = trial_data.get("has_adaptive_design", 0)
        features["biomarker_driven"] = trial_data.get("biomarker_driven", 0)
        features["has_patient_reported_outcomes"] = trial_data.get("has_patient_reported_outcomes", 0)

        # Override/fill with user inputs
        if user_inputs:
            for key, value in user_inputs.items():
                if value is not None:
                    features[key] = value

        return features

    def validate_features(self, features: Dict[str, Any]) -> List[str]:
        """
        Validate feature completeness and return list of missing features.

        Args:
            features: Feature dictionary

        Returns:
            List of missing required feature names (empty if complete)
        """
        missing = []

        for feature_name in self.required_features:
            if feature_name not in features or features[feature_name] is None:
                missing.append(feature_name)

        return missing

    def generate_prompts(self, missing_features: List[str]) -> Dict[str, Dict]:
        """
        Generate UI prompts for missing features.

        Args:
            missing_features: List of missing feature names

        Returns:
            Dictionary mapping feature name to prompt config
        """
        prompts = {}

        for feature_name in missing_features:
            if feature_name in FEATURE_PROMPTS:
                prompts[feature_name] = FEATURE_PROMPTS[feature_name]
            else:
                # Generic prompt for unknown features
                prompts[feature_name] = {
                    "question": f"Please provide: {feature_name}",
                    "type": "text",
                    "required": True,
                    "help": "",
                }

        return prompts

    def fill_defaults(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill in default values for optional features that are missing.

        Args:
            features: Feature dictionary

        Returns:
            Updated feature dictionary with defaults
        """
        defaults = {
            "num_conditions": 1,
            "num_secondary_outcomes": 2,
            "has_age_restriction": 1,
            "has_collaborators": 0,
            "num_collaborators": 0,
            "is_interventional": 1,
            "criteria_length": 100,
            "has_adaptive_design": 0,
            "biomarker_driven": 0,
            "has_patient_reported_outcomes": 0,
        }

        for feature_name, default_value in defaults.items():
            if feature_name not in features or features[feature_name] is None:
                features[feature_name] = default_value

        # Special handling for num_locations: estimate from enrollment if missing
        if "num_locations" not in features or features["num_locations"] is None:
            features["num_locations"] = self.estimate_num_locations(
                features.get("enrollment", 100)
            )
            logger.info(
                f"Estimated num_locations={features['num_locations']} "
                f"based on enrollment={features.get('enrollment')}"
            )

        # Derived feature: is_multicenter
        if "is_multicenter" not in features or features["is_multicenter"] is None:
            features["is_multicenter"] = 1 if features.get("num_locations", 1) > 1 else 0

        return features

    def estimate_num_locations(self, enrollment: int) -> int:
        """
        Estimate number of locations based on enrollment target.

        Rule of thumb: 10-15 patients per site on average.

        Args:
            enrollment: Target enrollment

        Returns:
            Estimated number of sites
        """
        if enrollment < 50:
            return 2  # 1-3 sites for small trials
        elif enrollment < 200:
            return max(5, enrollment // 15)  # ~15 patients/site
        elif enrollment < 500:
            return max(15, enrollment // 12)  # ~12 patients/site
        else:
            return max(40, enrollment // 10)  # ~10 patients/site for large trials

    def to_numpy(
        self, features_list: List[Dict[str, Any]], feature_order: Optional[List[str]] = None
    ) -> tuple[np.ndarray, List[str]]:
        """
        Convert list of feature dicts to numpy array for model input.

        Args:
            features_list: List of feature dictionaries
            feature_order: Order of features (if None, inferred from first dict)

        Returns:
            Tuple of (numpy array, feature names)
        """
        if not features_list:
            return np.array([]), []

        if feature_order is None:
            feature_order = list(features_list[0].keys())

        # Convert to 2D array
        X = np.array([[features[f] for f in feature_order] for features in features_list])

        return X, feature_order

    def _encode_phase(self, phase: Optional[TrialPhase]) -> int:
        """Encode trial phase as numeric value."""
        phase_map = {
            None: 0,
            TrialPhase.EARLY_PHASE_1: 1,
            TrialPhase.PHASE_1: 2,
            TrialPhase.PHASE_2: 3,
            TrialPhase.PHASE_3: 4,
            TrialPhase.PHASE_4: 5,
        }
        return phase_map.get(phase, 0)

    def _parse_phase(self, phase_str: str) -> Optional[TrialPhase]:
        """Parse phase string to TrialPhase enum."""
        phase_str_upper = phase_str.upper().replace(" ", "_")

        try:
            return TrialPhase[phase_str_upper]
        except KeyError:
            # Try common variations
            mapping = {
                "EARLY_PHASE_1": TrialPhase.EARLY_PHASE_1,
                "PHASE_1": TrialPhase.PHASE_1,
                "PHASE_2": TrialPhase.PHASE_2,
                "PHASE_3": TrialPhase.PHASE_3,
                "PHASE_4": TrialPhase.PHASE_4,
                "PHASE1": TrialPhase.PHASE_1,
                "PHASE2": TrialPhase.PHASE_2,
                "PHASE3": TrialPhase.PHASE_3,
                "PHASE4": TrialPhase.PHASE_4,
            }
            return mapping.get(phase_str_upper, None)

    def load_schema(self, schema_path: str) -> None:
        """Load feature schema from JSON file."""
        with open(schema_path, "r") as f:
            schema_data = json.load(f)

        # Parse feature definitions
        features = []
        for feat_data in schema_data["features"]:
            features.append(
                FeatureDefinition(
                    name=feat_data["name"],
                    type=feat_data["type"],
                    required=feat_data["required"],
                    encoding=feat_data.get("encoding"),
                    default=feat_data.get("default"),
                    min_value=feat_data.get("min_value"),
                    max_value=feat_data.get("max_value"),
                    importance=feat_data.get("importance"),
                    description=feat_data.get("description", ""),
                )
            )

        self.schema = FeatureSchema(
            version=schema_data["version"],
            model_type=schema_data["model_type"],
            trained_on=schema_data["trained_on"],
            n_trials=schema_data["n_trials"],
            features=features,
            feature_order=schema_data["feature_order"],
        )

        self.required_features = [f.name for f in features if f.required]
        logger.info(f"Loaded feature schema from {schema_path}")

    def save_schema(
        self,
        schema_path: str,
        version: str = "1.0.0",
        model_type: str = "XGBoost",
        n_trials: int = 0,
        feature_importance: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Save feature schema to JSON file.

        Args:
            schema_path: Path to save schema
            version: Schema version
            model_type: Type of model
            n_trials: Number of trials used for training
            feature_importance: Optional dict of feature importances
        """
        from datetime import datetime

        features_data = []
        for feature_name in self.required_features:
            feat_data = {
                "name": feature_name,
                "type": "numeric",  # Simplified for now
                "required": True,
                "importance": (
                    feature_importance.get(feature_name, 0.0) if feature_importance else 0.0
                ),
            }
            features_data.append(feat_data)

        schema_data = {
            "version": version,
            "model_type": model_type,
            "trained_on": datetime.now().strftime("%Y-%m-%d"),
            "n_trials": n_trials,
            "features": features_data,
            "feature_order": self.required_features,
        }

        Path(schema_path).parent.mkdir(parents=True, exist_ok=True)
        with open(schema_path, "w") as f:
            json.dump(schema_data, f, indent=2)

        logger.info(f"Saved feature schema to {schema_path}")

    def _detect_adaptive_design(self, trial: ClinicalTrial) -> int:
        """
        Detect if trial uses adaptive design based on keywords.

        Looks for mentions of: basket, umbrella, platform, master protocol,
        adaptive, interim analysis with adaptation.

        Args:
            trial: ClinicalTrial object

        Returns:
            1 if adaptive design detected, 0 otherwise
        """
        # Check title and description for keywords
        text_to_search = " ".join([
            trial.title.lower() if trial.title else "",
            trial.brief_summary.lower() if trial.brief_summary else "",
            trial.detailed_description.lower() if trial.detailed_description else "",
        ])

        adaptive_keywords = [
            "adaptive",
            "basket",
            "umbrella",
            "platform",
            "master protocol",
            "seamless",
            "group sequential",
            "interim adaptation",
        ]

        return 1 if any(kw in text_to_search for kw in adaptive_keywords) else 0

    def _detect_biomarker_driven(self, trial: ClinicalTrial) -> int:
        """
        Detect if trial is biomarker-driven.

        Looks for mentions of: biomarker, companion diagnostic, genomic,
        molecular, PD-L1, HER2, EGFR, etc.

        Args:
            trial: ClinicalTrial object

        Returns:
            1 if biomarker-driven detected, 0 otherwise
        """
        text_to_search = " ".join([
            trial.title.lower() if trial.title else "",
            trial.brief_summary.lower() if trial.brief_summary else "",
            trial.eligibility_criteria.lower() if trial.eligibility_criteria else "",
        ])

        biomarker_keywords = [
            "biomarker",
            "companion diagnostic",
            "genomic",
            "molecular",
            "pd-l1",
            "her2",
            "egfr",
            "kras",
            "braf",
            "alk",
            "gene expression",
            "mutation",
            "precision medicine",
            "targeted therapy",
        ]

        return 1 if any(kw in text_to_search for kw in biomarker_keywords) else 0

    def _detect_pro(self, trial: ClinicalTrial) -> int:
        """
        Detect if trial includes patient-reported outcomes (PROs).

        Looks for mentions of: quality of life, QOL, PRO, patient-reported,
        symptom score, functional assessment, etc.

        Args:
            trial: ClinicalTrial object

        Returns:
            1 if PROs detected, 0 otherwise
        """
        # Check secondary outcomes for PRO keywords
        outcomes_text = " ".join([
            trial.primary_outcome.lower() if trial.primary_outcome else "",
            " ".join([so.lower() for so in trial.secondary_outcomes if isinstance(so, str)]),
        ])

        pro_keywords = [
            "quality of life",
            "qol",
            "patient-reported",
            "pro ",
            "eortc",
            "fact-",
            "promis",
            "symptom",
            "functional assessment",
            "health-related quality",
        ]

        return 1 if any(kw in outcomes_text for kw in pro_keywords) else 0
