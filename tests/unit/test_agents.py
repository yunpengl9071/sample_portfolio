"""Unit tests for agent implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from trialsense.agents.base import BaseAgent
from trialsense.agents.outcome_agent import OutcomePredictionAgent
from trialsense.agents.site_matching_agent import SiteMatchingAgent
from trialsense.agents.orchestrator import TrialSenseOrchestrator, TrialAnalysisState


class TestBaseAgent:
    """Test suite for BaseAgent."""

    def test_base_agent_initialization(self):
        """Test that BaseAgent initializes with required components."""

        class TestAgent(BaseAgent):
            def _get_default_system_prompt(self):
                return "Test prompt"

        with patch.object(BaseAgent, '_create_llm') as mock_llm:
            mock_llm.return_value = MagicMock()
            agent = TestAgent(tools=[], verbose=False)

            assert agent.tools == []
            assert agent.system_prompt == "Test prompt"
            assert agent.agent_executor is not None

    def test_base_agent_requires_system_prompt(self):
        """Test that BaseAgent requires _get_default_system_prompt implementation."""

        with pytest.raises(TypeError):
            # Should raise because _get_default_system_prompt is abstract
            BaseAgent(tools=[])


class TestOutcomePredictionAgent:
    """Test suite for OutcomePredictionAgent."""

    @patch('trialsense.agents.outcome_agent.TrialVectorStore')
    @patch('trialsense.agents.outcome_agent.OutcomePredictor')
    @patch.object(BaseAgent, '_create_llm')
    def test_outcome_agent_initialization(self, mock_llm, mock_predictor, mock_vector_store):
        """Test OutcomePredictionAgent initializes with correct tools."""
        mock_llm.return_value = MagicMock()
        mock_vector_store.return_value = MagicMock()
        mock_predictor.return_value = MagicMock()

        agent = OutcomePredictionAgent(verbose=False)

        # Should have multiple tools
        assert len(agent.tools) > 0

        # Check tool names
        tool_names = [tool.name for tool in agent.tools]
        assert "get_trial_details" in tool_names
        assert "search_clinical_trials" in tool_names
        assert "predict_trial_outcome" in tool_names

    @patch('trialsense.agents.outcome_agent.TrialVectorStore')
    @patch('trialsense.agents.outcome_agent.OutcomePredictor')
    @patch.object(BaseAgent, '_create_llm')
    def test_outcome_agent_system_prompt(self, mock_llm, mock_predictor, mock_vector_store):
        """Test that outcome agent has appropriate system prompt."""
        mock_llm.return_value = MagicMock()
        mock_vector_store.return_value = MagicMock()
        mock_predictor.return_value = MagicMock()

        agent = OutcomePredictionAgent(verbose=False)

        prompt = agent._get_default_system_prompt()

        assert "clinical trial analyst" in prompt.lower()
        assert "outcome prediction" in prompt.lower()
        assert "shap" in prompt.lower()


class TestSiteMatchingAgent:
    """Test suite for SiteMatchingAgent."""

    @patch.object(BaseAgent, '_create_llm')
    def test_site_matching_agent_initialization(self, mock_llm):
        """Test SiteMatchingAgent initializes with correct tools."""
        mock_llm.return_value = MagicMock()

        agent = SiteMatchingAgent(verbose=False)

        # Should have site-related tools
        assert len(agent.tools) > 0

        tool_names = [tool.name for tool in agent.tools]
        assert "search_clinical_sites" in tool_names
        assert "evaluate_site_performance" in tool_names

    @patch.object(BaseAgent, '_create_llm')
    def test_site_matching_agent_system_prompt(self, mock_llm):
        """Test that site matching agent has appropriate system prompt."""
        mock_llm.return_value = MagicMock()

        agent = SiteMatchingAgent(verbose=False)

        prompt = agent._get_default_system_prompt()

        assert "site selection" in prompt.lower()
        assert "matching" in prompt.lower()
        assert "geographic" in prompt.lower()


class TestTrialSenseOrchestrator:
    """Test suite for TrialSenseOrchestrator."""

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_orchestrator_initialization(self, mock_site_agent, mock_outcome_agent):
        """Test orchestrator initializes workflow."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        assert orchestrator.outcome_agent is not None
        assert orchestrator.site_matching_agent is not None
        assert orchestrator.workflow is not None
        assert orchestrator.app is not None

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_route_query_outcome_prediction(self, mock_site_agent, mock_outcome_agent):
        """Test query routing for outcome prediction."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        state = {
            "query": "Predict outcome for NCT12345678",
            "messages": [],
            "task_type": "chat",
            "nct_id": None,
            "outcome_prediction": None,
            "site_recommendations": None,
            "final_response": None,
            "reasoning_trace": [],
        }

        result = orchestrator._route_query(state)

        assert result["task_type"] == "outcome_prediction"
        assert result["nct_id"] == "NCT12345678"
        assert len(result["reasoning_trace"]) > 0

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_route_query_site_matching(self, mock_site_agent, mock_outcome_agent):
        """Test query routing for site matching."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        state = {
            "query": "Recommend sites for lung cancer trial",
            "messages": [],
            "task_type": "chat",
            "nct_id": None,
            "outcome_prediction": None,
            "site_recommendations": None,
            "final_response": None,
            "reasoning_trace": [],
        }

        result = orchestrator._route_query(state)

        assert result["task_type"] == "site_matching"

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_route_query_comprehensive(self, mock_site_agent, mock_outcome_agent):
        """Test query routing for comprehensive analysis."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        state = {
            "query": "Analyze trial NCT12345678 comprehensively",
            "messages": [],
            "task_type": "chat",
            "nct_id": None,
            "outcome_prediction": None,
            "site_recommendations": None,
            "final_response": None,
            "reasoning_trace": [],
        }

        result = orchestrator._route_query(state)

        assert result["task_type"] == "comprehensive"
        assert result["nct_id"] == "NCT12345678"

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_synthesize_results_with_outcome(self, mock_site_agent, mock_outcome_agent):
        """Test result synthesis with outcome prediction."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        state = {
            "query": "Test query",
            "messages": [],
            "task_type": "outcome_prediction",
            "nct_id": "NCT12345678",
            "outcome_prediction": "Success probability: 75%",
            "site_recommendations": None,
            "final_response": None,
            "reasoning_trace": ["Step 1"],
        }

        result = orchestrator._synthesize_results(state)

        assert "OUTCOME ANALYSIS" in result["final_response"]
        assert "Success probability: 75%" in result["final_response"]

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_synthesize_results_comprehensive(self, mock_site_agent, mock_outcome_agent):
        """Test result synthesis for comprehensive analysis."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        state = {
            "query": "Test query",
            "messages": [],
            "task_type": "comprehensive",
            "nct_id": "NCT12345678",
            "outcome_prediction": "Success probability: 75%",
            "site_recommendations": "Top site: Johns Hopkins",
            "final_response": None,
            "reasoning_trace": ["Step 1", "Step 2"],
        }

        result = orchestrator._synthesize_results(state)

        assert "OUTCOME ANALYSIS" in result["final_response"]
        assert "SITE RECOMMENDATIONS" in result["final_response"]
        assert "Success probability: 75%" in result["final_response"]
        assert "Johns Hopkins" in result["final_response"]

    @patch('trialsense.agents.orchestrator.OutcomePredictionAgent')
    @patch('trialsense.agents.orchestrator.SiteMatchingAgent')
    def test_synthesize_results_no_analysis(self, mock_site_agent, mock_outcome_agent):
        """Test result synthesis with no specialized analysis."""
        mock_outcome_agent.return_value = MagicMock()
        mock_site_agent.return_value = MagicMock()

        orchestrator = TrialSenseOrchestrator()

        state = {
            "query": "Hello",
            "messages": [],
            "task_type": "chat",
            "nct_id": None,
            "outcome_prediction": None,
            "site_recommendations": None,
            "final_response": None,
            "reasoning_trace": [],
        }

        result = orchestrator._synthesize_results(state)

        assert "I can help you analyze clinical trials" in result["final_response"]
