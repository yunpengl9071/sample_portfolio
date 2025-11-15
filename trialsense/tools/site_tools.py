"""Tools for site search and evaluation."""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class SiteSearchInput(BaseModel):
    """Input schema for site search tool."""

    therapeutic_area: str = Field(
        description="Therapeutic area or disease (e.g., 'oncology', 'cardiology')"
    )
    region: Optional[str] = Field(
        default=None,
        description="Geographic region (e.g., 'Northeast US', 'California')"
    )
    top_k: int = Field(
        default=10,
        description="Number of sites to return",
        ge=1,
        le=50,
    )


class SiteSearchTool(BaseTool):
    """
    Tool for searching clinical trial sites.

    Searches a database of clinical trial sites with filters for
    therapeutic area, geography, and capabilities.
    """

    name: str = "search_clinical_sites"
    description: str = """
    Search for clinical trial sites matching specific criteria.

    This tool searches a database of active clinical trial sites and returns
    sites with relevant experience and capabilities.

    Filters:
    - Therapeutic area/disease expertise
    - Geographic region
    - Infrastructure capabilities

    Returns site names, locations, therapeutic areas, and brief capabilities.

    Example: search_clinical_sites(therapeutic_area="lung cancer", region="Northeast US")
    """
    args_schema: Type[BaseModel] = SiteSearchInput
    return_direct: bool = False

    def _run(
        self,
        therapeutic_area: str,
        region: Optional[str] = None,
        top_k: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute synchronously."""
        logger.info(f"Searching sites: {therapeutic_area}, region={region}")

        # Mock data - in production, would query real site database
        mock_sites = self._get_mock_sites(therapeutic_area, region, top_k)

        output = []
        output.append(f"Found {len(mock_sites)} sites for {therapeutic_area}:\n")

        for i, site in enumerate(mock_sites, 1):
            output.append(f"{i}. {site['name']}")
            output.append(f"   Location: {site['location']}")
            output.append(f"   Therapeutic Areas: {', '.join(site['areas'])}")
            output.append(f"   Infrastructure: {site['infrastructure']}")
            output.append(f"   Active Trials: {site['active_trials']}")
            output.append("")

        return "\n".join(output)

    async def _arun(self, *args, **kwargs) -> str:
        """Execute asynchronously."""
        return self._run(*args, **kwargs)

    def _get_mock_sites(
        self, therapeutic_area: str, region: Optional[str], top_k: int
    ) -> list[dict]:
        """Generate mock site data."""
        # This would be replaced with real database query
        mock_sites = [
            {
                "name": "Johns Hopkins Sidney Kimmel Cancer Center",
                "location": "Baltimore, MD",
                "areas": ["Oncology", "Immunotherapy", "Hematology"],
                "infrastructure": "Advanced imaging, genomics lab, phase I unit",
                "active_trials": 147,
            },
            {
                "name": "Dana-Farber Cancer Institute",
                "location": "Boston, MA",
                "areas": ["Oncology", "Precision Medicine"],
                "infrastructure": "Translational research lab, imaging center",
                "active_trials": 132,
            },
            {
                "name": "Memorial Sloan Kettering Cancer Center",
                "location": "New York, NY",
                "areas": ["Oncology", "Surgical Oncology", "Immunotherapy"],
                "infrastructure": "Comprehensive cancer center, early phase unit",
                "active_trials": 189,
            },
            {
                "name": "MD Anderson Cancer Center",
                "location": "Houston, TX",
                "areas": ["Oncology", "Immunology", "Precision Medicine"],
                "infrastructure": "Phase I-IV capabilities, translational lab",
                "active_trials": 203,
            },
            {
                "name": "Mayo Clinic - Rochester",
                "location": "Rochester, MN",
                "areas": ["Multi-specialty", "Oncology", "Cardiology"],
                "infrastructure": "Comprehensive capabilities, genomics",
                "active_trials": 165,
            },
        ]

        return mock_sites[:top_k]


class SitePerformanceInput(BaseModel):
    """Input schema for site performance evaluation."""

    site_name: str = Field(
        description="Name of the clinical trial site to evaluate"
    )
    therapeutic_area: Optional[str] = Field(
        default=None,
        description="Focus on specific therapeutic area"
    )


class SitePerformanceTool(BaseTool):
    """
    Tool for evaluating historical site performance.

    Analyzes site's track record on previous trials including:
    - Enrollment rates
    - Protocol compliance
    - Retention metrics
    - Timeline adherence
    """

    name: str = "evaluate_site_performance"
    description: str = """
    Evaluate the historical performance of a clinical trial site.

    This tool analyzes a site's track record on previous clinical trials,
    providing metrics on:
    - Enrollment performance (vs. targets)
    - Average enrollment rate (patients/month)
    - Protocol compliance
    - Patient retention
    - Common therapeutic areas

    Returns performance summary with specific trial examples.

    Example: evaluate_site_performance(site_name="Johns Hopkins Cancer Center")
    """
    args_schema: Type[BaseModel] = SitePerformanceInput
    return_direct: bool = False

    def _run(
        self,
        site_name: str,
        therapeutic_area: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute synchronously."""
        logger.info(f"Evaluating performance: {site_name}")

        # Mock data - in production, would query trial outcomes database
        performance = self._get_mock_performance(site_name, therapeutic_area)

        output = []
        output.append(f"=== Performance Profile: {site_name} ===\n")

        output.append("--- Overall Metrics ---")
        output.append(f"Total Trials Completed: {performance['total_trials']}")
        output.append(
            f"Average Enrollment vs Target: {performance['enrollment_pct']:.0%}"
        )
        output.append(
            f"Avg Enrollment Rate: {performance['enrollment_rate']:.1f} patients/month"
        )
        output.append(f"Protocol Compliance: {performance['compliance']:.0%}")
        output.append(f"Patient Retention: {performance['retention']:.0%}\n")

        output.append("--- Recent Trial Examples ---")
        for trial in performance['recent_trials']:
            output.append(f"Trial: {trial['nct_id']} ({trial['indication']})")
            output.append(
                f"  Enrolled: {trial['enrolled']} / {trial['target']} "
                f"({trial['enrolled']/trial['target']:.0%})"
            )
            output.append(f"  Timeline: {trial['months']} months")
            output.append(f"  Outcome: {trial['outcome']}\n")

        output.append("--- Strengths ---")
        for strength in performance['strengths']:
            output.append(f"  ✓ {strength}")

        output.append("\n--- Considerations ---")
        for consideration in performance['considerations']:
            output.append(f"  ⚠ {consideration}")

        return "\n".join(output)

    async def _arun(self, *args, **kwargs) -> str:
        """Execute asynchronously."""
        return self._run(*args, **kwargs)

    def _get_mock_performance(
        self, site_name: str, therapeutic_area: Optional[str]
    ) -> dict:
        """Generate mock performance data."""
        # This would be replaced with real data
        return {
            "total_trials": 47,
            "enrollment_pct": 1.15,
            "enrollment_rate": 4.2,
            "compliance": 0.96,
            "retention": 0.89,
            "recent_trials": [
                {
                    "nct_id": "NCT04123456",
                    "indication": "NSCLC immunotherapy",
                    "enrolled": 45,
                    "target": 35,
                    "months": 8,
                    "outcome": "Met primary endpoint",
                },
                {
                    "nct_id": "NCT03987654",
                    "indication": "Breast cancer HER2+",
                    "enrolled": 28,
                    "target": 30,
                    "months": 11,
                    "outcome": "Completed successfully",
                },
            ],
            "strengths": [
                "Consistently exceeds enrollment targets",
                "Strong patient retention (89%)",
                "Experienced principal investigators",
                "Dedicated research coordinators",
            ],
            "considerations": [
                "Currently running 3 competing immunotherapy trials",
                "IRB approval typically takes 8-10 weeks",
                "May require dedicated trial coordinator",
            ],
        }
