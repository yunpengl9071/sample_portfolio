#!/usr/bin/env python
"""
Script to populate the vector store with clinical trials embeddings.

This creates a searchable database of trials for RAG retrieval.
"""

import asyncio
from pathlib import Path

from trialsense.data.clinical_trials_client import ClinicalTrialsClient
from trialsense.data.vector_store import TrialVectorStore
from trialsense.data.models import TrialPhase
from trialsense.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


async def fetch_trials_for_indexing(
    conditions: list[str] = None,
    max_per_condition: int = 100
) -> list:
    """
    Fetch diverse set of trials for indexing.

    Args:
        conditions: List of medical conditions to fetch
        max_per_condition: Max trials per condition

    Returns:
        List of ClinicalTrial objects
    """
    if conditions is None:
        conditions = [
            "lung cancer",
            "breast cancer",
            "diabetes",
            "heart disease",
            "alzheimer's disease",
            "parkinson's disease",
            "rheumatoid arthritis",
            "multiple sclerosis",
            "covid-19",
            "depression",
        ]

    logger.info(f"Fetching trials for {len(conditions)} conditions...")

    all_trials = []
    seen_nct_ids = set()

    async with ClinicalTrialsClient() as client:
        for condition in conditions:
            logger.info(f"  Fetching {condition} trials...")

            trials = await client.search_trials(
                condition=condition,
                max_results=max_per_condition,
            )

            # Deduplicate
            for trial in trials:
                if trial.nct_id not in seen_nct_ids:
                    all_trials.append(trial)
                    seen_nct_ids.add(trial.nct_id)

            logger.info(f"    Found {len(trials)} trials ({len(all_trials)} total unique)")

    logger.info(f"Fetched {len(all_trials)} unique trials")
    return all_trials


async def index_trials(trials: list, vector_store: TrialVectorStore):
    """
    Index trials in the vector store.

    Args:
        trials: List of trials to index
        vector_store: Vector store instance
    """
    logger.info(f"Indexing {len(trials)} trials...")

    # Index in batches for progress tracking
    batch_size = 50

    for i in range(0, len(trials), batch_size):
        batch = trials[i:i+batch_size]
        await vector_store.add_trials(batch)

        logger.info(f"  Indexed {min(i+batch_size, len(trials))}/{len(trials)} trials")

    final_count = vector_store.count()
    logger.info(f"Vector store now contains {final_count} trials")


async def test_vector_store(vector_store: TrialVectorStore):
    """
    Test the vector store with sample queries.

    Args:
        vector_store: Vector store instance
    """
    logger.info("\nTesting vector store with sample queries...")

    test_queries = [
        "lung cancer immunotherapy trials",
        "phase 3 diabetes prevention",
        "alzheimer's disease biomarkers",
    ]

    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")

        results = await vector_store.search(query, top_k=3)

        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. {result['nct_id']} (similarity: {result['score']:.3f})")
            logger.info(f"     {result['text'][:100]}...")


async def main():
    """Main indexing pipeline."""
    setup_logging()

    logger.info("="*80)
    logger.info("TrialSense AI - Vector Store Population")
    logger.info("="*80)

    # 1. Initialize vector store
    logger.info("\n[1/4] Initializing vector store...")
    vector_store = TrialVectorStore()

    current_count = vector_store.count()
    logger.info(f"Current trial count: {current_count}")

    # 2. Fetch trials
    logger.info("\n[2/4] Fetching trials from ClinicalTrials.gov...")
    trials = await fetch_trials_for_indexing(max_per_condition=50)

    # 3. Index trials
    logger.info("\n[3/4] Indexing trials in vector store...")
    await index_trials(trials, vector_store)

    # 4. Test
    logger.info("\n[4/4] Testing vector store...")
    await test_vector_store(vector_store)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("Indexing Complete!")
    logger.info("="*80)
    logger.info(f"Total trials indexed: {vector_store.count()}")
    logger.info(f"Vector store location: {vector_store.persist_dir}")
    logger.info("\nThe vector store is now ready for semantic search!")


if __name__ == "__main__":
    asyncio.run(main())
