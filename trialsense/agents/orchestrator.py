"""LangGraph orchestrator for multi-agent coordination."""

from typing import TypedDict, Annotated, Sequence, Literal, Optional
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from trialsense.agents.outcome_agent import OutcomePredictionAgent
from trialsense.agents.site_matching_agent import SiteMatchingAgent
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class TrialAnalysisState(TypedDict):
    """State for the trial analysis workflow."""

    # Input
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    nct_id: Optional[str]

    # Processing
    task_type: Literal["outcome_prediction", "site_matching", "comprehensive", "chat"]

    # Outputs from specialized agents
    outcome_prediction: Optional[str]
    site_recommendations: Optional[str]

    # Final output
    final_response: Optional[str]
    reasoning_trace: list[str]


class TrialSenseOrchestrator:
    """
    Main orchestrator coordinating multiple specialized agents using LangGraph.

    Workflow:
    1. User query → Route to appropriate agent(s)
    2. Outcome Prediction Agent → Analyze trial success probability
    3. Site Matching Agent → Recommend optimal sites
    4. Synthesizer → Combine results into cohesive response

    The orchestrator maintains state and handles:
    - Query routing
    - Agent coordination
    - Result synthesis
    - Error handling
    """

    def __init__(
        self,
        outcome_agent: Optional[OutcomePredictionAgent] = None,
        site_matching_agent: Optional[SiteMatchingAgent] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            outcome_agent: Outcome prediction agent instance
            site_matching_agent: Site matching agent instance
        """
        self.outcome_agent = outcome_agent or OutcomePredictionAgent()
        self.site_matching_agent = site_matching_agent or SiteMatchingAgent()

        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(TrialAnalysisState)

        # Add nodes
        workflow.add_node("router", self._route_query)
        workflow.add_node("outcome_predictor", self._predict_outcome)
        workflow.add_node("site_matcher", self._match_sites)
        workflow.add_node("synthesizer", self._synthesize_results)

        # Set entry point
        workflow.set_entry_point("router")

        # Add conditional edges from router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "outcome_prediction": "outcome_predictor",
                "site_matching": "site_matcher",
                "comprehensive": "outcome_predictor",  # Start with outcome
                "chat": "synthesizer",
            },
        )

        # For comprehensive analysis: outcome → sites → synthesizer
        workflow.add_conditional_edges(
            "outcome_predictor",
            self._after_outcome,
            {
                "site_matching": "site_matcher",
                "synthesizer": "synthesizer",
            },
        )

        # Sites → synthesizer
        workflow.add_edge("site_matcher", "synthesizer")

        # Synthesizer → END
        workflow.add_edge("synthesizer", END)

        return workflow

    def _route_query(self, state: TrialAnalysisState) -> TrialAnalysisState:
        """Analyze query and determine routing."""
        logger.info(f"Routing query: {state['query']}")

        query_lower = state["query"].lower()

        # Extract NCT ID if present
        nct_id = None
        words = state["query"].split()
        for word in words:
            if word.upper().startswith("NCT") and len(word) >= 10:
                nct_id = word.upper()
                break

        # Determine task type based on keywords
        if any(kw in query_lower for kw in ["predict", "outcome", "success", "probability"]):
            task_type = "outcome_prediction"
        elif any(kw in query_lower for kw in ["site", "location", "recommend", "match"]):
            task_type = "site_matching"
        elif any(kw in query_lower for kw in ["analyze", "comprehensive", "evaluate"]):
            task_type = "comprehensive"
        else:
            task_type = "chat"

        state["task_type"] = task_type
        state["nct_id"] = nct_id
        state["reasoning_trace"] = [f"Routed to: {task_type}"]

        logger.info(f"Task type: {task_type}, NCT ID: {nct_id}")

        return state

    def _route_decision(self, state: TrialAnalysisState) -> str:
        """Decision function for routing."""
        return state["task_type"]

    def _after_outcome(self, state: TrialAnalysisState) -> str:
        """Decide next step after outcome prediction."""
        if state["task_type"] == "comprehensive":
            return "site_matching"
        return "synthesizer"

    async def _predict_outcome(self, state: TrialAnalysisState) -> TrialAnalysisState:
        """Run outcome prediction agent."""
        logger.info("Running outcome prediction agent")

        try:
            result = await self.outcome_agent.arun(
                input_text=state["query"],
                chat_history=state.get("messages", []),
            )

            state["outcome_prediction"] = result["output"]
            state["reasoning_trace"].append("Completed outcome prediction")

        except Exception as e:
            logger.error(f"Outcome prediction failed: {e}")
            state["outcome_prediction"] = f"Error in outcome prediction: {e}"
            state["reasoning_trace"].append(f"Error: {e}")

        return state

    async def _match_sites(self, state: TrialAnalysisState) -> TrialAnalysisState:
        """Run site matching agent."""
        logger.info("Running site matching agent")

        try:
            # Enhance query with context from outcome prediction if available
            query = state["query"]
            if state.get("outcome_prediction") and state["nct_id"]:
                query = f"""Based on trial {state['nct_id']}, recommend optimal sites.

Context from outcome analysis:
{state['outcome_prediction'][:500]}

Original query: {query}
"""

            result = await self.site_matching_agent.arun(
                input_text=query,
                chat_history=state.get("messages", []),
            )

            state["site_recommendations"] = result["output"]
            state["reasoning_trace"].append("Completed site matching")

        except Exception as e:
            logger.error(f"Site matching failed: {e}")
            state["site_recommendations"] = f"Error in site matching: {e}"
            state["reasoning_trace"].append(f"Error: {e}")

        return state

    def _synthesize_results(self, state: TrialAnalysisState) -> TrialAnalysisState:
        """Synthesize results from all agents."""
        logger.info("Synthesizing results")

        parts = []

        # Add outcome prediction if available
        if state.get("outcome_prediction"):
            parts.append("=== OUTCOME ANALYSIS ===\n")
            parts.append(state["outcome_prediction"])
            parts.append("\n")

        # Add site recommendations if available
        if state.get("site_recommendations"):
            parts.append("=== SITE RECOMMENDATIONS ===\n")
            parts.append(state["site_recommendations"])
            parts.append("\n")

        # If no specialized analysis, provide a general response
        if not parts:
            parts.append(
                "I can help you analyze clinical trials. You can:\n"
                "- Predict trial outcomes: 'Predict outcome for NCT12345678'\n"
                "- Match trial sites: 'Recommend sites for lung cancer trial'\n"
                "- Comprehensive analysis: 'Analyze trial NCT12345678'\n"
            )

        state["final_response"] = "\n".join(parts)
        state["reasoning_trace"].append("Synthesis complete")

        return state

    async def arun(self, query: str) -> dict:
        """
        Run the orchestrator asynchronously.

        Args:
            query: User query

        Returns:
            Dict with final_response and reasoning_trace
        """
        logger.info(f"Orchestrator received query: {query}")

        initial_state = TrialAnalysisState(
            messages=[HumanMessage(content=query)],
            query=query,
            nct_id=None,
            task_type="chat",
            outcome_prediction=None,
            site_recommendations=None,
            final_response=None,
            reasoning_trace=[],
        )

        # Run the workflow
        final_state = await self.app.ainvoke(initial_state)

        return {
            "response": final_state["final_response"],
            "reasoning_trace": final_state["reasoning_trace"],
            "task_type": final_state["task_type"],
        }

    def run(self, query: str) -> dict:
        """
        Run the orchestrator synchronously.

        Args:
            query: User query

        Returns:
            Dict with final_response and reasoning_trace
        """
        import asyncio
        return asyncio.run(self.arun(query))
