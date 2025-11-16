"""Unit tests for ClinicalTrialsClient."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import httpx

from trialsense.data.clinical_trials_client import (
    ClinicalTrialsClient,
    RateLimitError,
)
from trialsense.data.models import ClinicalTrial, TrialPhase, TrialStatus


class TestClinicalTrialsClient:
    """Test suite for ClinicalTrialsClient."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager initialization."""
        async with ClinicalTrialsClient() as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_parse_trial(self, sample_trial_data):
        """Test parsing raw API data into ClinicalTrial model."""
        client = ClinicalTrialsClient()
        trial = client._parse_trial(sample_trial_data)

        assert isinstance(trial, ClinicalTrial)
        assert trial.nct_id == "NCT12345678"
        assert trial.title == "A Phase 3 Study of Novel Cancer Treatment"
        assert trial.status == TrialStatus.RECRUITING
        assert trial.phase == TrialPhase.PHASE_3
        assert trial.sponsor.name == "Test Pharma Inc"
        assert len(trial.collaborators) == 1
        assert len(trial.conditions) == 2
        assert len(trial.interventions) == 2
        assert len(trial.locations) == 1
        assert trial.enrollment == 300

    @pytest.mark.asyncio
    async def test_parse_trial_with_missing_fields(self):
        """Test parsing trial data with missing optional fields."""
        minimal_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT99999999",
                    "briefTitle": "Minimal Trial",
                },
                "statusModule": {
                    "overallStatus": "UNKNOWN",
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {
                        "name": "Unknown Sponsor",
                    },
                },
                "designModule": {
                    "studyType": "OBSERVATIONAL",
                },
            },
            "hasResults": False,
        }

        client = ClinicalTrialsClient()
        trial = client._parse_trial(minimal_data)

        assert trial.nct_id == "NCT99999999"
        assert trial.title == "Minimal Trial"
        assert trial.phase is None
        assert trial.enrollment is None
        assert len(trial.conditions) == 0
        assert len(trial.interventions) == 0

    @pytest.mark.asyncio
    async def test_get_trial_success(self, sample_trial_data):
        """Test successful retrieval of a single trial."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"studies": [sample_trial_data]}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(return_value=mock_response)

            trial = await client.get_trial("NCT12345678")

            assert isinstance(trial, ClinicalTrial)
            assert trial.nct_id == "NCT12345678"
            client._client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trial_not_found(self):
        """Test handling of trial not found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"studies": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError, match="not found"):
                await client.get_trial("NCT00000000")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test handling of rate limit errors with retry."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=MagicMock(),
            response=mock_response,
        )

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(RateLimitError):
                await client.get_trial("NCT12345678")

    @pytest.mark.asyncio
    async def test_http_error_retry(self):
        """Test retry logic on HTTP errors."""
        # First 2 calls fail, third succeeds
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 503
        mock_fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service unavailable",
            request=MagicMock(),
            response=mock_fail_response,
        )

        mock_success_response = MagicMock()
        mock_success_response.json.return_value = {
            "studies": [{"protocolSection": {"identificationModule": {"nctId": "NCT12345678", "briefTitle": "Test"}}}]
        }
        mock_success_response.status_code = 200
        mock_success_response.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(
                side_effect=[
                    mock_fail_response,
                    mock_fail_response,
                    mock_success_response,
                ]
            )

            # Should succeed after retries
            trial = await client.get_trial("NCT12345678")
            assert trial.nct_id == "NCT12345678"
            assert client._client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_search_trials_basic(self, sample_trial_data):
        """Test basic trial search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "studies": [sample_trial_data],
            "nextPageToken": None,
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(return_value=mock_response)

            trials = await client.search_trials(
                query="cancer",
                max_results=10,
            )

            assert len(trials) == 1
            assert trials[0].nct_id == "NCT12345678"

    @pytest.mark.asyncio
    async def test_search_trials_with_filters(self, sample_trial_data):
        """Test trial search with multiple filters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "studies": [sample_trial_data],
            "nextPageToken": None,
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(return_value=mock_response)

            trials = await client.search_trials(
                condition="lung cancer",
                phase=[TrialPhase.PHASE_3],
                status=[TrialStatus.RECRUITING],
                max_results=10,
            )

            assert len(trials) == 1

            # Verify query parameters were constructed correctly
            call_args = client._client.get.call_args
            params = call_args.kwargs.get("params", {})
            assert "query.term" in params
            assert "SEARCH[Condition]lung cancer" in params["query.term"]
            assert "AREA[Phase]PHASE3" in params["query.term"]

    @pytest.mark.asyncio
    async def test_search_trials_pagination(self, sample_trial_data):
        """Test trial search with pagination."""
        # First page
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {
            "studies": [sample_trial_data] * 50,
            "nextPageToken": "token123",
        }
        mock_response_1.status_code = 200
        mock_response_1.raise_for_status = MagicMock()

        # Second page
        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {
            "studies": [sample_trial_data] * 50,
            "nextPageToken": None,
        }
        mock_response_2.status_code = 200
        mock_response_2.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(
                side_effect=[mock_response_1, mock_response_2]
            )

            trials = await client.search_trials(
                query="cancer",
                max_results=75,
            )

            # Should retrieve 75 trials across 2 pages
            assert len(trials) == 75
            assert client._client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_search_trials_parse_error_handling(self, sample_trial_data):
        """Test that parse errors for individual trials don't fail entire search."""
        bad_trial_data = {"protocolSection": {}}  # Missing required fields

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "studies": [bad_trial_data, sample_trial_data],
            "nextPageToken": None,
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        async with ClinicalTrialsClient() as client:
            client._client.get = AsyncMock(return_value=mock_response)

            trials = await client.search_trials(query="cancer", max_results=10)

            # Both trials are parsed - bad one has defaults, good one has real data
            assert len(trials) == 2
            # The second one should be the good trial
            assert trials[1].nct_id == "NCT12345678"
            # First one has minimal/default data
            assert trials[0].nct_id == ""

    @pytest.mark.asyncio
    async def test_rate_limiting_wait(self):
        """Test that rate limiting properly delays requests."""
        async with ClinicalTrialsClient(rate_limit=2) as client:
            # Make 2 requests (within rate limit)
            await client._wait_for_rate_limit()
            await client._wait_for_rate_limit()

            # Should have 2 request timestamps
            assert len(client._request_times) == 2

            # Third request should wait if we exceed rate limit
            await client._wait_for_rate_limit()
            # After waiting, old timestamps are cleared
            assert len(client._request_times) >= 1


class TestTrialPhaseEnum:
    """Test TrialPhase enum."""

    def test_phase_values(self):
        """Test that phase enum has expected values."""
        assert TrialPhase.PHASE_1 == "PHASE1"
        assert TrialPhase.PHASE_3 == "PHASE3"

    def test_phase_from_string(self):
        """Test creating phase from string."""
        phase = TrialPhase("PHASE2")
        assert phase == TrialPhase.PHASE_2


class TestTrialStatusEnum:
    """Test TrialStatus enum."""

    def test_status_values(self):
        """Test that status enum has expected values."""
        assert TrialStatus.RECRUITING == "RECRUITING"
        assert TrialStatus.COMPLETED == "COMPLETED"

    def test_status_from_string(self):
        """Test creating status from string."""
        status = TrialStatus("TERMINATED")
        assert status == TrialStatus.TERMINATED
