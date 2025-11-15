"""Client for ClinicalTrials.gov API v2."""

import asyncio
from typing import Optional, Any
from datetime import datetime, timedelta

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from trialsense.config import get_settings
from trialsense.utils.logging import get_logger
from trialsense.data.models import (
    ClinicalTrial,
    TrialPhase,
    TrialStatus,
    Sponsor,
    Condition,
    Intervention,
    Location,
)

logger = get_logger(__name__)


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class ClinicalTrialsClient:
    """
    Client for interacting with ClinicalTrials.gov API v2.

    Features:
    - Automatic retry with exponential backoff
    - Rate limiting
    - Structured data parsing
    - Async support for batch operations

    Example:
        >>> client = ClinicalTrialsClient()
        >>> trial = await client.get_trial("NCT04567890")
        >>> trials = await client.search_trials(query="lung cancer", max_results=100)
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        rate_limit: Optional[int] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the ClinicalTrials.gov API client.

        Args:
            api_base: API base URL (defaults to settings)
            rate_limit: Requests per minute (defaults to settings)
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        self.api_base = api_base or settings.clinicaltrials_api_base
        self.rate_limit = rate_limit or settings.clinicaltrials_rate_limit
        self.timeout = timeout

        # Rate limiting state
        self._request_times: list[datetime] = []
        self._lock = asyncio.Lock()

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ClinicalTrialsClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.api_base,
            timeout=self.timeout,
            headers={"User-Agent": "TrialSense-AI/0.1.0"},
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _wait_for_rate_limit(self) -> None:
        """Implement rate limiting using token bucket algorithm."""
        async with self._lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self._request_times = [
                t for t in self._request_times if now - t < timedelta(minutes=1)
            ]

            if len(self._request_times) >= self.rate_limit:
                # Calculate wait time
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    self._request_times = []

            self._request_times.append(now)

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        retry=retry_if_exception_type((httpx.HTTPError, RateLimitError)),
        reraise=True,
    )
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request with retry logic.

        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: On HTTP errors
            RateLimitError: On rate limit exceeded
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        await self._wait_for_rate_limit()

        try:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Request failed: {e}")
            raise

    def _parse_trial(self, data: dict[str, Any]) -> ClinicalTrial:
        """
        Parse raw API response into ClinicalTrial model.

        Args:
            data: Raw trial data from API

        Returns:
            Parsed ClinicalTrial object
        """
        protocol_section = data.get("protocolSection", {})
        id_module = protocol_section.get("identificationModule", {})
        status_module = protocol_section.get("statusModule", {})
        sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
        design_module = protocol_section.get("designModule", {})
        conditions_module = protocol_section.get("conditionsModule", {})
        interventions_module = protocol_section.get("armsInterventionsModule", {})
        eligibility_module = protocol_section.get("eligibilityModule", {})
        contacts_module = protocol_section.get("contactsLocationsModule", {})
        outcomes_module = protocol_section.get("outcomesModule", {})
        description_module = protocol_section.get("descriptionModule", {})

        # Parse sponsor
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        sponsor = Sponsor(
            name=lead_sponsor.get("name", "Unknown"),
            type=lead_sponsor.get("class"),
        )

        # Parse collaborators
        collaborators = [
            Sponsor(name=c.get("name", ""), type=c.get("class"))
            for c in sponsor_module.get("collaborators", [])
        ]

        # Parse conditions
        conditions = [
            Condition(name=c)
            for c in conditions_module.get("conditions", [])
        ]

        # Parse interventions
        interventions = [
            Intervention(
                type=i.get("type", ""),
                name=i.get("name", ""),
                description=i.get("description"),
            )
            for i in interventions_module.get("interventions", [])
        ]

        # Parse locations
        locations = [
            Location(
                facility=loc.get("facility", ""),
                city=loc.get("city"),
                state=loc.get("state"),
                country=loc.get("country", ""),
                zip_code=loc.get("zip"),
                status=loc.get("status"),
            )
            for loc in contacts_module.get("locations", [])
        ]

        # Parse phases
        phases = design_module.get("phases", [])
        phase = TrialPhase(phases[0]) if phases else None

        # Parse dates
        def parse_date(date_struct: dict) -> Optional[datetime]:
            if not date_struct:
                return None
            try:
                year = date_struct.get("year")
                month = date_struct.get("month", 1)
                day = date_struct.get("day", 1)
                if year:
                    return datetime(year, month, day).date()
            except (ValueError, TypeError):
                pass
            return None

        start_date = parse_date(status_module.get("startDateStruct"))
        completion_date = parse_date(status_module.get("completionDateStruct"))
        primary_completion_date = parse_date(
            status_module.get("primaryCompletionDateStruct")
        )

        return ClinicalTrial(
            nct_id=id_module.get("nctId", ""),
            title=id_module.get("officialTitle") or id_module.get("briefTitle", ""),
            status=TrialStatus(status_module.get("overallStatus", "UNKNOWN")),
            phase=phase,
            sponsor=sponsor,
            collaborators=collaborators,
            study_type=design_module.get("studyType", ""),
            enrollment=status_module.get("enrollmentInfo", {}).get("count"),
            allocation=design_module.get("designInfo", {}).get("allocation"),
            intervention_model=design_module.get("designInfo", {}).get(
                "interventionModel"
            ),
            primary_purpose=design_module.get("designInfo", {}).get("primaryPurpose"),
            masking=design_module.get("designInfo", {}).get("maskingInfo", {}).get(
                "masking"
            ),
            conditions=conditions,
            interventions=interventions,
            eligibility_criteria=eligibility_module.get("eligibilityCriteria"),
            minimum_age=eligibility_module.get("minimumAge"),
            maximum_age=eligibility_module.get("maximumAge"),
            gender=eligibility_module.get("sex"),
            start_date=start_date,
            completion_date=completion_date,
            primary_completion_date=primary_completion_date,
            locations=locations,
            primary_outcome=outcomes_module.get("primaryOutcomes", [{}])[0].get(
                "measure"
            )
            if outcomes_module.get("primaryOutcomes")
            else None,
            secondary_outcomes=[
                o.get("measure", "")
                for o in outcomes_module.get("secondaryOutcomes", [])
            ],
            brief_summary=description_module.get("briefSummary"),
            detailed_description=description_module.get("detailedDescription"),
            keywords=conditions_module.get("keywords", []),
            has_results=data.get("hasResults", False),
        )

    async def get_trial(self, nct_id: str) -> ClinicalTrial:
        """
        Get a single trial by NCT ID.

        Args:
            nct_id: NCT identifier (e.g., "NCT04567890")

        Returns:
            ClinicalTrial object

        Example:
            >>> async with ClinicalTrialsClient() as client:
            ...     trial = await client.get_trial("NCT04567890")
        """
        logger.info(f"Fetching trial {nct_id}")

        data = await self._make_request(
            f"/studies/{nct_id}",
            params={"format": "json"},
        )

        studies = data.get("studies", [])
        if not studies:
            raise ValueError(f"Trial {nct_id} not found")

        return self._parse_trial(studies[0])

    async def search_trials(
        self,
        query: Optional[str] = None,
        condition: Optional[str] = None,
        intervention: Optional[str] = None,
        phase: Optional[list[TrialPhase]] = None,
        status: Optional[list[TrialStatus]] = None,
        max_results: int = 100,
        page_size: int = 100,
    ) -> list[ClinicalTrial]:
        """
        Search for trials with various filters.

        Args:
            query: Free text query
            condition: Medical condition filter
            intervention: Intervention/treatment filter
            phase: List of trial phases to include
            status: List of trial statuses to include
            max_results: Maximum number of results to return
            page_size: Results per page (max 100)

        Returns:
            List of ClinicalTrial objects

        Example:
            >>> async with ClinicalTrialsClient() as client:
            ...     trials = await client.search_trials(
            ...         condition="lung cancer",
            ...         phase=[TrialPhase.PHASE_3],
            ...         max_results=50
            ...     )
        """
        logger.info(f"Searching trials: query={query}, condition={condition}")

        params: dict[str, Any] = {
            "format": "json",
            "pageSize": min(page_size, 100),
        }

        # Build query filter
        filters = []
        if query:
            filters.append(f"SEARCH[BasicSearch]{query}")
        if condition:
            filters.append(f"SEARCH[Condition]{condition}")
        if intervention:
            filters.append(f"SEARCH[Intervention]{intervention}")
        if phase:
            phase_str = ",".join([p.value for p in phase])
            filters.append(f"AREA[Phase]{phase_str}")
        if status:
            status_str = ",".join([s.value for s in status])
            filters.append(f"AREA[OverallStatus]{status_str}")

        if filters:
            params["query.term"] = " AND ".join(filters)

        trials = []
        page_token = None

        while len(trials) < max_results:
            if page_token:
                params["pageToken"] = page_token

            data = await self._make_request("/studies", params=params)

            studies = data.get("studies", [])
            for study in studies:
                if len(trials) >= max_results:
                    break
                try:
                    trial = self._parse_trial(study)
                    trials.append(trial)
                except Exception as e:
                    logger.warning(f"Failed to parse trial: {e}")
                    continue

            # Check if there are more pages
            page_token = data.get("nextPageToken")
            if not page_token or len(studies) == 0:
                break

        logger.info(f"Found {len(trials)} trials")
        return trials
