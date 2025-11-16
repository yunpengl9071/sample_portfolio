"""Unit tests for LangChain tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from trialsense.tools.trial_search import TrialSearchTool, SimilarTrialsTool
from trialsense.tools.trial_retrieval import TrialRetrievalTool
from trialsense.tools.prediction_tools import PredictOutcomeTool, ExplainPredictionTool
from trialsense.tools.site_tools import SiteSearchTool, SitePerformanceTool


class TestTrialSearchTool:
    """Test suite for TrialSearchTool."""

    @pytest.mark.asyncio
    async def test_trial_search_tool_basic(self):
        """Test basic trial search functionality."""
        mock_vector_store = MagicMock()
        mock_vector_store.search = AsyncMock(return_value=[
            {
                "nct_id": "NCT12345678",
                "score": 0.95,
                "metadata": {
                    "phase": "PHASE3",
                    "status": "RECRUITING",
                    "enrollment": 300,
                    "therapeutic_area": "Oncology",
                },
                "text": "Phase 3 lung cancer trial..."
            }
        ])

        tool = TrialSearchTool(vector_store=mock_vector_store)

        result = await tool._arun("lung cancer immunotherapy", top_k=10)

        assert "NCT12345678" in result
        assert "PHASE3" in result
        assert "Oncology" in result
        mock_vector_store.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_trial_search_tool_no_results(self):
        """Test trial search with no results."""
        mock_vector_store = MagicMock()
        mock_vector_store.search = AsyncMock(return_value=[])

        tool = TrialSearchTool(vector_store=mock_vector_store)

        result = await tool._arun("nonexistent disease", top_k=10)

        assert "No trials found" in result

    @pytest.mark.asyncio
    async def test_trial_search_tool_with_filters(self):
        """Test trial search with phase and status filters."""
        mock_vector_store = MagicMock()
        mock_vector_store.search = AsyncMock(return_value=[])

        tool = TrialSearchTool(vector_store=mock_vector_store)

        await tool._arun("cancer", top_k=5, phase="PHASE3", status="RECRUITING")

        mock_vector_store.search.assert_called_once_with(
            query="cancer",
            top_k=5,
            phase="PHASE3",
            status="RECRUITING"
        )


class TestSimilarTrialsTool:
    """Test suite for SimilarTrialsTool."""

    @pytest.mark.asyncio
    async def test_similar_trials_tool_success(self):
        """Test finding similar trials."""
        mock_vector_store = MagicMock()
        mock_vector_store.get_similar_trials = AsyncMock(return_value=[
            {
                "nct_id": "NCT98765432",
                "score": 0.89,
                "metadata": {"phase": "PHASE3", "status": "COMPLETED"},
                "text": "Similar trial..."
            }
        ])

        tool = SimilarTrialsTool(vector_store=mock_vector_store)

        result = await tool._arun("NCT12345678", top_k=10)

        assert "NCT98765432" in result
        assert "Similar" in result

    @pytest.mark.asyncio
    async def test_similar_trials_tool_not_found(self):
        """Test similar trials when reference trial not found."""
        mock_vector_store = MagicMock()
        mock_vector_store.get_similar_trials = AsyncMock(
            side_effect=ValueError("Trial not found")
        )

        tool = SimilarTrialsTool(vector_store=mock_vector_store)

        result = await tool._arun("NCT00000000", top_k=10)

        assert "Error" in result


class TestTrialRetrievalTool:
    """Test suite for TrialRetrievalTool."""

    @pytest.mark.asyncio
    async def test_trial_retrieval_success(self, sample_clinical_trial):
        """Test successful trial retrieval."""
        with patch('trialsense.tools.trial_retrieval.ClinicalTrialsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_trial = AsyncMock(return_value=sample_clinical_trial)
            mock_client_class.return_value = mock_client

            tool = TrialRetrievalTool()
            result = await tool._arun("NCT12345678")

            assert "NCT12345678" in result
            assert "Phase 3" in result
            assert "Test Pharma Inc" in result

    @pytest.mark.asyncio
    async def test_trial_retrieval_not_found(self):
        """Test trial retrieval when trial doesn't exist."""
        with patch('trialsense.tools.trial_retrieval.ClinicalTrialsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_trial = AsyncMock(side_effect=ValueError("Trial not found"))
            mock_client_class.return_value = mock_client

            tool = TrialRetrievalTool()
            result = await tool._arun("NCT00000000")

            assert "Error" in result


class TestPredictOutcomeTool:
    """Test suite for PredictOutcomeTool."""

    @pytest.mark.asyncio
    async def test_predict_outcome_success(self, sample_clinical_trial):
        """Test successful outcome prediction."""
        from trialsense.models.outcome_predictor import PredictionResult

        mock_predictor = MagicMock()
        mock_predictor.predict.return_value = PredictionResult(
            success_probability=0.67,
            confidence_interval=(0.59, 0.75),
            feature_importance={"enrollment": 0.15, "phase_numeric": 0.12},
            shap_explanation={},
            risk_factors=["num_interventions=2 (SHAP: -0.08)"],
            positive_factors=["is_randomized=1 (SHAP: 0.12)"]
        )

        with patch('trialsense.tools.prediction_tools.ClinicalTrialsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_trial = AsyncMock(return_value=sample_clinical_trial)
            mock_client_class.return_value = mock_client

            tool = PredictOutcomeTool(outcome_model=mock_predictor)
            result = await tool._arun("NCT12345678")

            assert "67.0%" in result or "67%" in result
            assert "Positive Factors" in result
            assert "Risk Factors" in result


class TestSiteSearchTool:
    """Test suite for SiteSearchTool."""

    def test_site_search_basic(self):
        """Test basic site search."""
        tool = SiteSearchTool()

        result = tool._run("oncology", region="Northeast US", top_k=5)

        assert "Johns Hopkins" in result or "Dana-Farber" in result
        assert "Oncology" in result

    def test_site_search_output_format(self):
        """Test site search output format."""
        tool = SiteSearchTool()

        result = tool._run("cardiology", top_k=3)

        # Should contain structured information
        assert "Location:" in result
        assert "Therapeutic Areas:" in result
        assert "Active Trials:" in result


class TestSitePerformanceTool:
    """Test suite for SitePerformanceTool."""

    def test_site_performance_evaluation(self):
        """Test site performance evaluation."""
        tool = SitePerformanceTool()

        result = tool._run("Johns Hopkins Cancer Center")

        assert "Performance Profile" in result
        assert "Overall Metrics" in result
        assert "Total Trials" in result
        assert "Enrollment" in result

    def test_site_performance_with_therapeutic_area(self):
        """Test site performance with therapeutic area filter."""
        tool = SitePerformanceTool()

        result = tool._run("Dana-Farber", therapeutic_area="oncology")

        assert "Performance Profile" in result
        # Mock data should still return results
        assert len(result) > 0


class TestToolInputValidation:
    """Test input validation for tools."""

    def test_trial_search_input_validation(self):
        """Test TrialSearchInput validation."""
        from trialsense.tools.trial_search import TrialSearchInput

        # Valid input
        valid_input = TrialSearchInput(query="cancer", top_k=10)
        assert valid_input.query == "cancer"
        assert valid_input.top_k == 10

        # Invalid top_k (too large)
        with pytest.raises(Exception):  # Pydantic ValidationError
            TrialSearchInput(query="cancer", top_k=100)

    def test_predict_outcome_input_validation(self):
        """Test PredictOutcomeInput validation."""
        from trialsense.tools.prediction_tools import PredictOutcomeInput

        # Valid input
        valid_input = PredictOutcomeInput(nct_id="NCT12345678")
        assert valid_input.nct_id == "NCT12345678"
