"""ML model for predicting clinical trial outcomes."""

from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import shap

from trialsense.data.models import ClinicalTrial, TrialPhase, TrialStatus
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """Result of outcome prediction."""

    success_probability: float
    confidence_interval: tuple[float, float]
    feature_importance: dict[str, float]
    shap_explanation: dict[str, Any]
    risk_factors: list[str]
    positive_factors: list[str]


class OutcomePredictor:
    """
    ML model for predicting clinical trial success probability.

    Uses XGBoost classifier with SHAP for interpretability.
    Predicts likelihood of trial completion with positive results.

    Training vs. Inference:
    - Training: Done once offline (10-50 minutes)
    - Inference: Fast predictions (<0.1 seconds per trial)

    The model can work in two modes:
    1. With pre-trained model: Full ML predictions
    2. Without training: Returns heuristic-based estimates (demo mode)

    Example:
        >>> # Option 1: Load pre-trained model
        >>> predictor = OutcomePredictor("models/outcome_model.json")
        >>> result = predictor.predict(trial)

        >>> # Option 2: Use without training (demo mode)
        >>> predictor = OutcomePredictor()  # No model loaded
        >>> result = predictor.predict(trial)  # Returns heuristic estimate
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the outcome predictor.

        Args:
            model_path: Path to saved model file (optional)
        """
        self.model: Optional[xgb.XGBClassifier] = None
        self.explainer: Optional[shap.TreeExplainer] = None
        self.feature_names: list[str] = []
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.is_trained = False

        if model_path and Path(model_path).exists():
            self.load(model_path)
            self.is_trained = True
            logger.info(f"✓ Loaded pre-trained model from {model_path}")
        else:
            self._initialize_model()
            if model_path:
                logger.warning(f"⚠ Model file not found: {model_path}")
            logger.info("Running in demo mode - predictions will use heuristics")

    def _initialize_model(self) -> None:
        """Initialize a new XGBoost model with default parameters."""
        self.model = xgb.XGBClassifier(
            objective="binary:logistic",
            max_depth=6,
            learning_rate=0.1,
            n_estimators=100,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="auc",
        )
        logger.info("Initialized new XGBoost model (untrained)")

    def _default_prediction(self, trial: ClinicalTrial) -> PredictionResult:
        """
        Generate heuristic-based prediction when model is not trained.

        Uses simple rules based on trial characteristics.
        Good enough for demo purposes.

        Args:
            trial: ClinicalTrial object

        Returns:
            PredictionResult with heuristic estimates
        """
        # Simple heuristic based on trial characteristics
        base_prob = 0.5

        # Phase bonus (later phases more likely to succeed)
        phase_bonus = {
            TrialPhase.PHASE_1: -0.1,
            TrialPhase.PHASE_2: 0.0,
            TrialPhase.PHASE_3: 0.1,
            TrialPhase.PHASE_4: 0.15,
        }.get(trial.phase, 0.0)

        # Design bonus (good design increases success)
        design_bonus = 0.0
        if trial.allocation == "RANDOMIZED":
            design_bonus += 0.05
        if trial.masking and trial.masking != "NONE":
            design_bonus += 0.05

        # Sponsor bonus (industry sponsors often have resources)
        sponsor_bonus = 0.05 if trial.sponsor.type == "INDUSTRY" else 0.0

        # Enrollment penalty (very large trials are harder)
        enrollment_penalty = -0.05 if trial.enrollment and trial.enrollment > 1000 else 0.0

        # Calculate final probability
        prob = base_prob + phase_bonus + design_bonus + sponsor_bonus + enrollment_penalty
        prob = max(0.2, min(0.8, prob))  # Clamp between 20-80%

        # Generate mock feature importance
        feature_importance = {
            "phase_numeric": phase_bonus,
            "is_randomized": 0.05 if trial.allocation == "RANDOMIZED" else -0.05,
            "enrollment_log": enrollment_penalty,
            "sponsor_type": sponsor_bonus,
        }

        # Identify factors
        positive_factors = []
        risk_factors = []

        if trial.phase in [TrialPhase.PHASE_3, TrialPhase.PHASE_4]:
            positive_factors.append(f"Later phase trial ({trial.phase})")
        if trial.allocation == "RANDOMIZED":
            positive_factors.append("Randomized design strengthens evidence")
        if trial.sponsor.type == "INDUSTRY":
            positive_factors.append("Industry sponsor (typically well-resourced)")

        if trial.enrollment and trial.enrollment > 1000:
            risk_factors.append(f"Large enrollment target (n={trial.enrollment})")
        if not trial.allocation:
            risk_factors.append("No allocation specified")

        return PredictionResult(
            success_probability=prob,
            confidence_interval=(max(0.0, prob - 0.1), min(1.0, prob + 0.1)),
            feature_importance=feature_importance,
            shap_explanation={
                "base_value": base_prob,
                "note": "Using heuristic-based prediction (model not trained)",
            },
            risk_factors=risk_factors or ["None identified"],
            positive_factors=positive_factors or ["None identified"],
        )

    def _extract_features(self, trial: ClinicalTrial) -> dict[str, Any]:
        """
        Extract predictive features from a trial.

        Args:
            trial: ClinicalTrial object

        Returns:
            Dictionary of features
        """
        features = {
            # Phase encoding
            "phase_numeric": self._encode_phase(trial.phase),

            # Enrollment metrics
            "enrollment": trial.enrollment or 0,
            "enrollment_log": np.log1p(trial.enrollment) if trial.enrollment else 0,

            # Sponsor features
            "sponsor_type": trial.sponsor.type or "UNKNOWN",
            "has_collaborators": len(trial.collaborators) > 0,
            "num_collaborators": len(trial.collaborators),

            # Study design
            "is_randomized": 1 if trial.allocation == "RANDOMIZED" else 0,
            "is_blinded": 1 if trial.masking and trial.masking != "NONE" else 0,
            "is_interventional": 1 if trial.study_type == "INTERVENTIONAL" else 0,

            # Complexity metrics
            "num_conditions": len(trial.conditions),
            "num_interventions": len(trial.interventions),
            "num_locations": len(trial.locations),
            "num_secondary_outcomes": len(trial.secondary_outcomes),

            # Eligibility breadth
            "has_age_restriction": 1 if trial.minimum_age or trial.maximum_age else 0,
            "criteria_length": len(trial.eligibility_criteria) if trial.eligibility_criteria else 0,

            # Status indicators
            "is_multicenter": 1 if len(trial.locations) > 1 else 0,

            # Therapeutic area (simplified)
            "therapeutic_area": trial.conditions[0].name if trial.conditions else "Unknown",
        }

        return features

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

    def _prepare_features_for_model(
        self, features: dict[str, Any], fit: bool = False
    ) -> np.ndarray:
        """
        Convert feature dict to model input array.

        Args:
            features: Feature dictionary
            fit: Whether to fit label encoders (for training)

        Returns:
            Feature array
        """
        # Define feature columns
        numeric_features = [
            "phase_numeric", "enrollment", "enrollment_log",
            "has_collaborators", "num_collaborators",
            "is_randomized", "is_blinded", "is_interventional",
            "num_conditions", "num_interventions", "num_locations",
            "num_secondary_outcomes", "has_age_restriction",
            "criteria_length", "is_multicenter",
        ]

        categorical_features = ["sponsor_type", "therapeutic_area"]

        # Extract numeric features
        X_numeric = [features[f] for f in numeric_features]

        # Encode categorical features
        X_categorical = []
        for cat_feat in categorical_features:
            value = features[cat_feat]

            if fit:
                if cat_feat not in self.label_encoders:
                    self.label_encoders[cat_feat] = LabelEncoder()
                    self.label_encoders[cat_feat].fit([value, "UNKNOWN"])

            if cat_feat in self.label_encoders:
                try:
                    encoded = self.label_encoders[cat_feat].transform([value])[0]
                except ValueError:
                    # Unknown category
                    encoded = 0
            else:
                encoded = 0

            X_categorical.append(encoded)

        # Combine all features
        X = np.array(X_numeric + X_categorical)

        if not self.feature_names:
            self.feature_names = numeric_features + categorical_features

        return X

    def train(
        self,
        trials: list[ClinicalTrial],
        labels: list[int],
        validation_split: float = 0.2,
    ) -> dict[str, float]:
        """
        Train the model on historical trial data.

        This is a ONE-TIME operation (or periodic refresh).
        NOT run on every user query!

        Args:
            trials: List of ClinicalTrial objects
            labels: Binary labels (1 = success, 0 = failure)
            validation_split: Fraction of data for validation

        Returns:
            Training metrics
        """
        logger.info(f"Training on {len(trials)} trials")

        # Extract features
        features_list = [self._extract_features(t) for t in trials]
        X = np.array([
            self._prepare_features_for_model(f, fit=True) for f in features_list
        ])
        y = np.array(labels)

        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Train model
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # Initialize SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        self.is_trained = True

        # Evaluate
        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        metrics = {
            "train_accuracy": train_score,
            "val_accuracy": val_score,
        }

        logger.info(f"Training complete: {metrics}")
        return metrics

    def predict(self, trial: ClinicalTrial) -> PredictionResult:
        """
        Predict outcome for a trial (FAST - <0.1 seconds).

        This runs on every user query. No training happens here!

        Args:
            trial: ClinicalTrial object

        Returns:
            PredictionResult with probability and explanations
        """
        if not self.model:
            raise ValueError("Model not initialized")

        # If model not trained, return heuristic prediction
        if not self.is_trained:
            logger.debug("Using heuristic prediction (model not trained)")
            return self._default_prediction(trial)

        # Extract and prepare features (fast)
        features = self._extract_features(trial)
        X = self._prepare_features_for_model(features, fit=False)
        X_reshaped = X.reshape(1, -1)

        # Predict probability (very fast)
        proba = self.model.predict_proba(X_reshaped)[0][1]

        # Calculate confidence interval
        ci_width = 0.1
        ci_lower = max(0.0, proba - ci_width)
        ci_upper = min(1.0, proba + ci_width)

        # Get SHAP values (fast)
        shap_values = None
        feature_importance = {}

        if self.explainer:
            shap_values = self.explainer.shap_values(X_reshaped)[0]
            feature_importance = dict(zip(
                self.feature_names,
                shap_values.tolist()
            ))

        # Identify risk and positive factors
        risk_factors, positive_factors = self._identify_factors(
            features, feature_importance
        )

        return PredictionResult(
            success_probability=float(proba),
            confidence_interval=(ci_lower, ci_upper),
            feature_importance=feature_importance,
            shap_explanation={
                "base_value": self.explainer.expected_value if self.explainer else 0.5,
                "shap_values": feature_importance,
            },
            risk_factors=risk_factors,
            positive_factors=positive_factors,
        )

    def _identify_factors(
        self,
        features: dict[str, Any],
        feature_importance: dict[str, float],
    ) -> tuple[list[str], list[str]]:
        """
        Identify key risk and positive factors.

        Args:
            features: Feature dictionary
            feature_importance: SHAP feature importances

        Returns:
            Tuple of (risk_factors, positive_factors)
        """
        risk_factors = []
        positive_factors = []

        # Sort features by absolute importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        for feat_name, importance in sorted_features[:5]:
            feat_value = features.get(feat_name)

            if importance < -0.05:
                # Negative contribution
                risk_factors.append(
                    f"{feat_name}={feat_value} (SHAP: {importance:.3f})"
                )
            elif importance > 0.05:
                # Positive contribution
                positive_factors.append(
                    f"{feat_name}={feat_value} (SHAP: {importance:.3f})"
                )

        return risk_factors, positive_factors

    def save(self, path: str) -> None:
        """Save trained model to file."""
        if not self.model:
            raise ValueError("No model to save")

        if not self.is_trained:
            logger.warning("Saving untrained model")

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str) -> None:
        """Load trained model from file."""
        if not Path(path).exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        self.model = xgb.XGBClassifier()
        self.model.load_model(path)
        self.explainer = shap.TreeExplainer(self.model)
        self.is_trained = True
        logger.info(f"Model loaded from {path}")
