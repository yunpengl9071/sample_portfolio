"""LangChain tools for searching clinical trials."""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from trialsense.data.vector_store import TrialVectorStore
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class TrialSearchInput(BaseModel):
    """Input schema for trial search tool."""

    query: str = Field(
        description="Natural language search query for clinical trials"
    )
    top_k: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=50,
    )
    phase: Optional[str] = Field(
        default=None,
        description="Filter by trial phase (PHASE1, PHASE2, PHASE3, PHASE4)",
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by trial status (RECRUITING, COMPLETED, etc.)",
    )


class TrialSearchTool(BaseTool):
    """
    Tool for semantic search over clinical trials database.

    Uses vector embeddings to find trials matching a natural language query.
    Supports filtering by phase, status, and other metadata.
    """

    name: str = "search_clinical_trials"
    description: str = """
    Search for clinical trials using natural language queries.

    This tool performs semantic search over 400,000+ clinical trials.
    Use it to find trials matching specific criteria like:
    - Disease/condition (e.g., "lung cancer", "diabetes")
    - Treatment type (e.g., "immunotherapy", "checkpoint inhibitor")
    - Study design features

    Returns trial summaries with NCT IDs, which can be used to retrieve full details.

    Example queries:
    - "phase 3 lung cancer immunotherapy trials"
    - "diabetes prevention studies with lifestyle interventions"
    - "pediatric rare disease trials"
    """
    args_schema: Type[BaseModel] = TrialSearchInput
    return_direct: bool = False

    vector_store: Optional[TrialVectorStore] = None

    def __init__(self, vector_store: Optional[TrialVectorStore] = None, **kwargs):
        """Initialize with vector store."""
        super().__init__(**kwargs)
        self.vector_store = vector_store or TrialVectorStore()

    def _run(
        self,
        query: str,
        top_k: int = 10,
        phase: Optional[str] = None,
        status: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the search synchronously."""
        import asyncio
        return asyncio.run(
            self._arun(query, top_k, phase, status, run_manager)
        )

    async def _arun(
        self,
        query: str,
        top_k: int = 10,
        phase: Optional[str] = None,
        status: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the search asynchronously."""
        logger.info(f"Searching trials: {query}")

        results = await self.vector_store.search(
            query=query,
            top_k=top_k,
            phase=phase,
            status=status,
        )

        if not results:
            return "No trials found matching the query."

        # Format results as structured text
        output_lines = [f"Found {len(results)} matching clinical trials:\n"]

        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            output_lines.append(
                f"{i}. NCT ID: {result['nct_id']} (Similarity: {result['score']:.2f})"
            )
            output_lines.append(f"   Phase: {meta.get('phase', 'Unknown')}")
            output_lines.append(f"   Status: {meta.get('status', 'Unknown')}")
            output_lines.append(f"   Enrollment: {meta.get('enrollment', 'N/A')}")
            output_lines.append(f"   Therapeutic Area: {meta.get('therapeutic_area', 'Unknown')}")
            output_lines.append(f"   Summary: {result['text'][:200]}...")
            output_lines.append("")

        return "\n".join(output_lines)


class SimilarTrialsInput(BaseModel):
    """Input schema for similar trials tool."""

    nct_id: str = Field(
        description="NCT ID of the reference trial"
    )
    top_k: int = Field(
        default=10,
        description="Number of similar trials to return",
        ge=1,
        le=20,
    )


class SimilarTrialsTool(BaseTool):
    """
    Tool for finding trials similar to a given trial.

    Uses vector similarity to find trials with similar:
    - Disease/condition
    - Interventions
    - Study design
    - Patient population
    """

    name: str = "find_similar_trials"
    description: str = """
    Find clinical trials similar to a given trial (by NCT ID).

    This tool identifies trials with similar characteristics including:
    - Medical condition
    - Treatment approach
    - Study design
    - Patient population

    Useful for:
    - Comparative analysis
    - Finding precedent trials
    - Understanding competitive landscape
    - Learning from similar successful trials

    Input: NCT ID (e.g., "NCT04567890")
    Output: List of similar trials with similarity scores
    """
    args_schema: Type[BaseModel] = SimilarTrialsInput
    return_direct: bool = False

    vector_store: Optional[TrialVectorStore] = None

    def __init__(self, vector_store: Optional[TrialVectorStore] = None, **kwargs):
        """Initialize with vector store."""
        super().__init__(**kwargs)
        self.vector_store = vector_store or TrialVectorStore()

    def _run(
        self,
        nct_id: str,
        top_k: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute synchronously."""
        import asyncio
        return asyncio.run(self._arun(nct_id, top_k, run_manager))

    async def _arun(
        self,
        nct_id: str,
        top_k: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute asynchronously."""
        logger.info(f"Finding trials similar to {nct_id}")

        try:
            results = await self.vector_store.get_similar_trials(
                nct_id=nct_id,
                top_k=top_k,
            )
        except ValueError as e:
            return f"Error: {e}"

        if not results:
            return f"No similar trials found for {nct_id}."

        # Format results
        output_lines = [
            f"Found {len(results)} trials similar to {nct_id}:\n"
        ]

        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            output_lines.append(
                f"{i}. {result['nct_id']} (Similarity: {result['score']:.2f})"
            )
            output_lines.append(f"   Phase: {meta.get('phase')}")
            output_lines.append(f"   Status: {meta.get('status')}")
            output_lines.append(f"   Summary: {result['text'][:150]}...")
            output_lines.append("")

        return "\n".join(output_lines)
