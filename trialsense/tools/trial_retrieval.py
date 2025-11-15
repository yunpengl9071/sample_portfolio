"""Tool for retrieving detailed trial information."""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from trialsense.data.clinical_trials_client import ClinicalTrialsClient
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class TrialRetrievalInput(BaseModel):
    """Input schema for trial retrieval tool."""

    nct_id: str = Field(
        description="NCT identifier of the trial to retrieve (e.g., 'NCT04567890')"
    )


class TrialRetrievalTool(BaseTool):
    """
    Tool for retrieving detailed information about a specific clinical trial.

    Fetches complete trial data from ClinicalTrials.gov API including:
    - Full protocol details
    - Eligibility criteria
    - Outcomes
    - Site locations
    - Sponsor information
    """

    name: str = "get_trial_details"
    description: str = """
    Retrieve detailed information about a specific clinical trial by NCT ID.

    This tool fetches comprehensive trial data including:
    - Complete title and description
    - Detailed eligibility criteria
    - Primary and secondary outcomes
    - Study design details
    - Site locations
    - Sponsor and collaborator information
    - Timeline and status
    - Enrollment numbers

    Use this when you need full details about a trial after finding it via search.

    Input: NCT ID (e.g., "NCT04567890")
    Output: Structured trial information
    """
    args_schema: Type[BaseModel] = TrialRetrievalInput
    return_direct: bool = False

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
        logger.info(f"Retrieving trial details for {nct_id}")

        try:
            async with ClinicalTrialsClient() as client:
                trial = await client.get_trial(nct_id)
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Failed to retrieve trial {nct_id}: {e}")
            return f"Error retrieving trial: {e}"

        # Format trial information
        output = []
        output.append(f"=== Trial Details: {trial.nct_id} ===\n")
        output.append(f"Title: {trial.title}")
        output.append(f"Status: {trial.status}")
        output.append(f"Phase: {trial.phase or 'N/A'}")
        output.append(f"Type: {trial.study_type}\n")

        output.append("--- Sponsorship ---")
        output.append(f"Lead Sponsor: {trial.sponsor.name} ({trial.sponsor.type})")
        if trial.collaborators:
            collab_names = [c.name for c in trial.collaborators[:3]]
            output.append(f"Collaborators: {', '.join(collab_names)}")
        output.append("")

        output.append("--- Study Design ---")
        output.append(f"Enrollment: {trial.enrollment or 'Not specified'}")
        if trial.allocation:
            output.append(f"Allocation: {trial.allocation}")
        if trial.intervention_model:
            output.append(f"Intervention Model: {trial.intervention_model}")
        if trial.primary_purpose:
            output.append(f"Primary Purpose: {trial.primary_purpose}")
        output.append("")

        output.append("--- Medical Details ---")
        if trial.conditions:
            conditions = [c.name for c in trial.conditions[:5]]
            output.append(f"Conditions: {', '.join(conditions)}")
        if trial.interventions:
            interventions = [f"{i.name} ({i.type})" for i in trial.interventions[:5]]
            output.append(f"Interventions: {', '.join(interventions)}")
        output.append("")

        if trial.eligibility_criteria:
            output.append("--- Eligibility Criteria ---")
            # Truncate if too long
            criteria = trial.eligibility_criteria[:500]
            if len(trial.eligibility_criteria) > 500:
                criteria += "..."
            output.append(criteria)
            output.append("")

        output.append("--- Outcomes ---")
        if trial.primary_outcome:
            output.append(f"Primary: {trial.primary_outcome}")
        if trial.secondary_outcomes:
            sec_outcomes = trial.secondary_outcomes[:3]
            output.append(f"Secondary: {', '.join(sec_outcomes)}")
        output.append("")

        if trial.locations:
            output.append(f"--- Locations ({len(trial.locations)} sites) ---")
            for loc in trial.locations[:5]:
                output.append(f"  • {loc.facility}, {loc.city}, {loc.country}")
            if len(trial.locations) > 5:
                output.append(f"  ... and {len(trial.locations) - 5} more")
            output.append("")

        output.append("--- Timeline ---")
        if trial.start_date:
            output.append(f"Start Date: {trial.start_date}")
        if trial.completion_date:
            output.append(f"Completion Date: {trial.completion_date}")
        output.append(f"Has Results: {'Yes' if trial.has_results else 'No'}")

        if trial.brief_summary:
            output.append("\n--- Summary ---")
            summary = trial.brief_summary[:300]
            if len(trial.brief_summary) > 300:
                summary += "..."
            output.append(summary)

        return "\n".join(output)
