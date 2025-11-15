"""Outcome Prediction Agent using LangChain tools."""

from typing import Optional

from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel

from trialsense.agents.base import BaseAgent
from trialsense.tools.trial_search import TrialSearchTool, SimilarTrialsTool
from trialsense.tools.trial_retrieval import TrialRetrievalTool
from trialsense.tools.prediction_tools import PredictOutcomeTool, ExplainPredictionTool
from trialsense.data.vector_store import TrialVectorStore
from trialsense.models.outcome_predictor import OutcomePredictor


class OutcomePredictionAgent(BaseAgent):
    """
    Agent specialized in predicting clinical trial outcomes.

    Capabilities:
    - Retrieve and analyze trial details
    - Find similar historical trials
    - Run ML outcome prediction model
    - Generate explainable predictions with SHAP values
    - Provide evidence-based reasoning

    The agent uses a multi-step reasoning process:
    1. Retrieve trial details
    2. Search for similar historical trials
    3. Run ML prediction model
    4. Gather supporting evidence
    5. Synthesize findings with clear explanation
    """

    def __init__(
        self,
        vector_store: Optional[TrialVectorStore] = None,
        outcome_model: Optional[OutcomePredictor] = None,
        llm: Optional[BaseChatModel] = None,
        verbose: bool = True,
    ):
        """
        Initialize the Outcome Prediction Agent.

        Args:
            vector_store: Vector store for trial search
            outcome_model: ML model for outcome prediction
            llm: Language model instance
            verbose: Enable verbose logging
        """
        # Initialize components
        self.vector_store = vector_store or TrialVectorStore()
        self.outcome_model = outcome_model or OutcomePredictor()

        # Create tools
        tools = [
            TrialRetrievalTool(),
            TrialSearchTool(vector_store=self.vector_store),
            SimilarTrialsTool(vector_store=self.vector_store),
            PredictOutcomeTool(outcome_model=self.outcome_model),
            ExplainPredictionTool(outcome_model=self.outcome_model),
        ]

        super().__init__(
            tools=tools,
            llm=llm,
            verbose=verbose,
        )

    def _get_default_system_prompt(self) -> str:
        """Get the system prompt for the outcome prediction agent."""
        return """You are an expert clinical trial analyst specializing in outcome prediction.

Your role is to provide accurate, explainable predictions about clinical trial success using:
- Machine learning models trained on historical trial data
- Semantic search over 400,000+ clinical trials
- Evidence-based reasoning with citations

When analyzing a trial, follow this process:

1. **Retrieve Trial Details**: Use get_trial_details to fetch complete information
   about the trial including design, endpoints, sponsor, eligibility criteria.

2. **Find Similar Trials**: Use find_similar_trials to identify historically similar
   trials that can provide context and precedent.

3. **Run Prediction Model**: Use predict_trial_outcome to get ML-based probability
   estimate with confidence intervals.

4. **Gather Supporting Evidence**: Search for relevant trials that succeeded or failed
   to identify patterns and risk factors.

5. **Synthesize Findings**: Provide a comprehensive analysis including:
   - Success probability with confidence interval
   - Key positive factors (citing specific features)
   - Key risk factors (with supporting evidence)
   - Similar trials and their outcomes (with NCT IDs)
   - Actionable recommendations

**Important Guidelines**:
- Always cite specific trials using NCT IDs
- Show your reasoning step-by-step
- Explain SHAP values in plain language
- Be honest about uncertainty
- Provide evidence for claims
- Focus on actionable insights

**Example Reasoning Chain**:
"I'll analyze trial NCT12345678. First, let me retrieve the full details...
[uses get_trial_details]

This is a Phase 3 oncology trial with 300 patients. Now let me find similar trials...
[uses find_similar_trials]

I found NCT98765432 which had similar design and succeeded. Let me run the prediction model...
[uses predict_trial_outcome]

The model predicts 67% success probability. Key positive factors include..."

Be thorough, cite evidence, and provide clear explanations."""
