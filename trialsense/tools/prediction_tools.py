"""Tools for ML-based outcome prediction."""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from trialsense.models.outcome_predictor import OutcomePredictor
from trialsense.data.clinical_trials_client import ClinicalTrialsClient
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class PredictOutcomeInput(BaseModel):
    """Input schema for outcome prediction tool."""

    nct_id: str = Field(
        description="NCT ID of the trial to predict"
    )


class PredictOutcomeTool(BaseTool):
    """
    Tool for predicting trial outcome using ML model.

    Uses XGBoost classifier to predict success probability
    based on trial features.
    """

    name: str = "predict_trial_outcome"
    description: str = """
    Predict the success probability of a clinical trial using machine learning.

    This tool runs an XGBoost model trained on historical trial data to estimate
    the likelihood of trial completion with positive results.

    Returns:
    - Success probability (0-1)
    - Confidence interval
    - Top positive and negative feature contributions
    - Risk factors and positive factors

    Input: NCT ID
    Output: Prediction with confidence interval and key factors
    """
    args_schema: Type[BaseModel] = PredictOutcomeInput
    return_direct: bool = False

    outcome_model: Optional[OutcomePredictor] = None

    def __init__(self, outcome_model: Optional[OutcomePredictor] = None, **kwargs):
        """Initialize with outcome model."""
        super().__init__(**kwargs)
        self.outcome_model = outcome_model or OutcomePredictor()

    def _run(
        self,
        nct_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute synchronously."""
        import asyncio
        return asyncio.run(self._arun(nct_id, run_manager))

    async def _arun(
        self,
        nct_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute asynchronously."""
        logger.info(f"Predicting outcome for {nct_id}")

        try:
            # Retrieve trial data
            async with ClinicalTrialsClient() as client:
                trial = await client.get_trial(nct_id)

            # Run prediction
            result = self.outcome_model.predict(trial)

            # Format output
            output = []
            output.append(f"=== Outcome Prediction for {nct_id} ===\n")
            output.append(f"Success Probability: {result.success_probability:.1%}")
            output.append(
                f"Confidence Interval: [{result.confidence_interval[0]:.1%}, "
                f"{result.confidence_interval[1]:.1%}]\n"
            )

            output.append("--- Positive Factors ---")
            if result.positive_factors:
                for factor in result.positive_factors[:5]:
                    output.append(f"  ✓ {factor}")
            else:
                output.append("  (none identified)")
            output.append("")

            output.append("--- Risk Factors ---")
            if result.risk_factors:
                for factor in result.risk_factors[:5]:
                    output.append(f"  ⚠ {factor}")
            else:
                output.append("  (none identified)")
            output.append("")

            # Feature importance summary
            if result.feature_importance:
                top_features = sorted(
                    result.feature_importance.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )[:5]

                output.append("--- Top Feature Contributions (SHAP) ---")
                for feat, val in top_features:
                    sign = "+" if val > 0 else ""
                    output.append(f"  {feat}: {sign}{val:.3f}")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Prediction failed for {nct_id}: {e}")
            return f"Error: Failed to predict outcome - {e}"


class ExplainPredictionInput(BaseModel):
    """Input schema for prediction explanation tool."""

    nct_id: str = Field(
        description="NCT ID of the trial"
    )
    focus: Optional[str] = Field(
        default=None,
        description="Specific aspect to explain (e.g., 'enrollment', 'design')"
    )


class ExplainPredictionTool(BaseTool):
    """
    Tool for explaining prediction in natural language.

    Provides detailed, interpretable explanation of why the model
    made a particular prediction using SHAP values.
    """

    name: str = "explain_prediction"
    description: str = """
    Get a detailed explanation of the outcome prediction.

    This tool provides human-readable explanations of:
    - Why the model predicts success or failure
    - Which trial features are most influential
    - How the trial compares to historical patterns
    - Specific recommendations based on the analysis

    Use this after predict_trial_outcome to understand the reasoning.

    Input: NCT ID (and optional focus area)
    Output: Natural language explanation
    """
    args_schema: Type[BaseModel] = ExplainPredictionInput
    return_direct: bool = False

    outcome_model: Optional[OutcomePredictor] = None

    def __init__(self, outcome_model: Optional[OutcomePredictor] = None, **kwargs):
        """Initialize with outcome model."""
        super().__init__(**kwargs)
        self.outcome_model = outcome_model or OutcomePredictor()

    def _run(
        self,
        nct_id: str,
        focus: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute synchronously."""
        import asyncio
        return asyncio.run(self._arun(nct_id, focus, run_manager))

    async def _arun(
        self,
        nct_id: str,
        focus: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute asynchronously."""
        logger.info(f"Explaining prediction for {nct_id}")

        try:
            # Get trial and prediction
            async with ClinicalTrialsClient() as client:
                trial = await client.get_trial(nct_id)

            result = self.outcome_model.predict(trial)

            # Generate explanation
            output = []
            output.append(f"=== Explanation for {nct_id} ===\n")

            # Overall assessment
            if result.success_probability > 0.7:
                assessment = "HIGH likelihood of success"
            elif result.success_probability > 0.5:
                assessment = "MODERATE likelihood of success"
            else:
                assessment = "LOWER likelihood of success"

            output.append(f"Overall Assessment: {assessment}")
            output.append(f"Predicted Probability: {result.success_probability:.1%}\n")

            # Explain key drivers
            output.append("--- Key Drivers of This Prediction ---\n")

            if result.positive_factors:
                output.append("POSITIVE FACTORS:")
                for i, factor in enumerate(result.positive_factors[:3], 1):
                    output.append(f"{i}. {factor}")
                    output.append(self._explain_factor(factor))
                output.append("")

            if result.risk_factors:
                output.append("RISK FACTORS:")
                for i, factor in enumerate(result.risk_factors[:3], 1):
                    output.append(f"{i}. {factor}")
                    output.append(self._explain_factor(factor))
                output.append("")

            # Recommendations
            output.append("--- Recommendations ---")
            recommendations = self._generate_recommendations(result, trial)
            for rec in recommendations:
                output.append(f"• {rec}")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Explanation failed for {nct_id}: {e}")
            return f"Error: Failed to generate explanation - {e}"

    def _explain_factor(self, factor: str) -> str:
        """Generate natural language explanation for a factor."""
        # Simple rule-based explanations
        # In production, could use LLM for more nuanced explanations

        explanations = {
            "enrollment": "Enrollment size affects trial power and feasibility",
            "phase_numeric": "Later phases typically have higher success rates",
            "is_randomized": "Randomization strengthens evidence quality",
            "is_blinded": "Blinding reduces bias in outcome assessment",
            "num_collaborators": "Collaborations can indicate resource availability",
            "is_multicenter": "Multi-center trials improve generalizability",
        }

        for key, explanation in explanations.items():
            if key in factor.lower():
                return f"   → {explanation}"

        return "   → Impacts success based on historical patterns"

    def _generate_recommendations(self, result, trial) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if result.success_probability < 0.5:
            recommendations.append(
                "Consider protocol refinements to address identified risk factors"
            )

        if "enrollment" in str(result.risk_factors).lower():
            recommendations.append(
                "Review enrollment strategy and site selection for feasibility"
            )

        if "endpoint" in str(result.risk_factors).lower():
            recommendations.append(
                "Simplify primary endpoint or add interim analyses"
            )

        if not recommendations:
            recommendations.append(
                "Trial design appears well-structured based on historical patterns"
            )

        return recommendations
