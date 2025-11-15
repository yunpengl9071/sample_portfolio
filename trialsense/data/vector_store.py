"""Vector store for clinical trials embeddings."""

from typing import Optional, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from trialsense.config import get_settings
from trialsense.utils.logging import get_logger
from trialsense.data.models import ClinicalTrial

logger = get_logger(__name__)


class TrialVectorStore:
    """
    Vector store for clinical trial embeddings.

    Uses ChromaDB for persistent storage and sentence-transformers for embeddings.
    Supports hybrid search combining semantic similarity and metadata filters.

    Example:
        >>> store = TrialVectorStore()
        >>> await store.add_trials([trial1, trial2, trial3])
        >>> results = await store.search("lung cancer immunotherapy", top_k=10)
    """

    def __init__(
        self,
        collection_name: str = "clinical_trials",
        persist_dir: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_dir: Directory for persistent storage
            embedding_model: Name of sentence-transformers model
        """
        settings = get_settings()
        self.collection_name = collection_name
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.embedding_model_name = embedding_model or settings.embedding_model

        # Ensure persist directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"Vector store initialized: {self.collection.count()} trials in collection"
        )

    def _create_trial_text(self, trial: ClinicalTrial) -> str:
        """
        Create searchable text representation of a trial.

        Args:
            trial: ClinicalTrial object

        Returns:
            Concatenated text for embedding
        """
        parts = [
            f"Title: {trial.title}",
            f"Phase: {trial.phase}" if trial.phase else "",
            f"Conditions: {', '.join(c.name for c in trial.conditions)}",
            f"Interventions: {', '.join(i.name for i in trial.interventions)}",
            f"Summary: {trial.brief_summary}" if trial.brief_summary else "",
            f"Sponsor: {trial.sponsor.name}",
            f"Status: {trial.status}",
        ]
        return " | ".join(p for p in parts if p)

    def _trial_to_metadata(self, trial: ClinicalTrial) -> dict[str, Any]:
        """
        Convert trial to metadata dict for filtering.

        Args:
            trial: ClinicalTrial object

        Returns:
            Metadata dictionary
        """
        return {
            "nct_id": trial.nct_id,
            "phase": trial.phase or "UNKNOWN",
            "status": trial.status,
            "sponsor_type": trial.sponsor.type or "UNKNOWN",
            "study_type": trial.study_type,
            "enrollment": trial.enrollment or 0,
            "has_results": trial.has_results,
            "therapeutic_area": trial.conditions[0].name if trial.conditions else "Unknown",
        }

    async def add_trials(self, trials: list[ClinicalTrial]) -> None:
        """
        Add trials to the vector store.

        Args:
            trials: List of ClinicalTrial objects
        """
        if not trials:
            return

        logger.info(f"Adding {len(trials)} trials to vector store")

        # Prepare data
        ids = [trial.nct_id for trial in trials]
        texts = [self._create_trial_text(trial) for trial in trials]
        metadatas = [self._trial_to_metadata(trial) for trial in trials]

        # Generate embeddings
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=len(trials) > 100,
            convert_to_numpy=True,
        ).tolist()

        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(trials), batch_size):
            batch_end = min(i + batch_size, len(trials))
            self.collection.upsert(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
                documents=texts[i:batch_end],
            )

        logger.info(f"Added {len(trials)} trials. Total: {self.collection.count()}")

    async def search(
        self,
        query: str,
        top_k: int = 10,
        phase: Optional[str] = None,
        status: Optional[str] = None,
        min_enrollment: Optional[int] = None,
        has_results: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar trials using semantic search.

        Args:
            query: Search query text
            top_k: Number of results to return
            phase: Filter by trial phase
            status: Filter by trial status
            min_enrollment: Minimum enrollment count
            has_results: Filter by results availability

        Returns:
            List of search results with metadata and scores
        """
        logger.info(f"Searching for: {query}")

        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True,
        ).tolist()

        # Build where filter
        where_filter = {}
        if phase:
            where_filter["phase"] = phase
        if status:
            where_filter["status"] = status
        if has_results is not None:
            where_filter["has_results"] = has_results

        # Execute search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None,
        )

        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, nct_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "nct_id": nct_id,
                    "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "metadata": results["metadatas"][0][i],
                    "text": results["documents"][0][i],
                })

        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results

    async def get_trial_by_id(self, nct_id: str) -> Optional[dict[str, Any]]:
        """
        Get a trial by NCT ID.

        Args:
            nct_id: NCT identifier

        Returns:
            Trial data or None if not found
        """
        results = self.collection.get(ids=[nct_id])

        if results["ids"]:
            return {
                "nct_id": results["ids"][0],
                "metadata": results["metadatas"][0],
                "text": results["documents"][0],
            }
        return None

    async def get_similar_trials(
        self,
        nct_id: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find trials similar to a given trial.

        Args:
            nct_id: NCT ID of the reference trial
            top_k: Number of similar trials to return

        Returns:
            List of similar trials
        """
        # Get the reference trial
        trial_data = await self.get_trial_by_id(nct_id)
        if not trial_data:
            raise ValueError(f"Trial {nct_id} not found")

        # Search using the trial's text
        results = await self.search(trial_data["text"], top_k=top_k + 1)

        # Remove the reference trial itself
        return [r for r in results if r["nct_id"] != nct_id][:top_k]

    def count(self) -> int:
        """Get total number of trials in the store."""
        return self.collection.count()

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
