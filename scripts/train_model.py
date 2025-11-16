#!/usr/bin/env python
"""
Script to train the outcome prediction model on historical trial data.

This script:
1. Fetches completed trials from ClinicalTrials.gov
2. Extracts features using FeatureEngineer
3. Trains XGBoost model with train/validation/test split
4. Saves model, feature schema, and test set for benchmarking
5. Evaluates performance on held-out test set

The test set is saved so users can benchmark predictions on known outcomes.
"""

import asyncio
from pathlib import Path
from datetime import datetime
import json
import pickle

from trialsense.data.clinical_trials_client import ClinicalTrialsClient
from trialsense.data.models import TrialPhase, TrialStatus
from trialsense.models.outcome_predictor import OutcomePredictor
from trialsense.models.outcome_labeling import determine_outcome, log_labeling_report
from trialsense.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


async def fetch_training_data(max_trials: int = 1000) -> tuple[list, list]:
    """
    Fetch historical trials for training.

    In production, this would:
    1. Query completed trials with known outcomes
    2. Label trials as success (1) or failure (0)
    3. Handle class imbalance

    Args:
        max_trials: Maximum number of trials to fetch

    Returns:
        Tuple of (trials, labels)
    """
    logger.info(f"Fetching up to {max_trials} trials for training...")

    async with ClinicalTrialsClient() as client:
        # Fetch trials from multiple phases and statuses
        # Include both completed and terminated to get diverse outcomes
        all_trials = []

        # Fetch completed Phase 2 and 3 trials (most reliable outcome data)
        for phase in [TrialPhase.PHASE_2, TrialPhase.PHASE_3]:
            completed = await client.search_trials(
                phase=[phase],
                status=[TrialStatus.COMPLETED],
                max_results=max_trials // 3,
            )
            all_trials.extend(completed)

        # Fetch terminated trials (failures)
        terminated = await client.search_trials(
            phase=[TrialPhase.PHASE_2, TrialPhase.PHASE_3],
            status=[TrialStatus.TERMINATED],
            max_results=max_trials // 3,
        )
        all_trials.extend(terminated)

        logger.info(f"Fetched {len(all_trials)} trials total")

    # Label trials using improved labeling logic
    trials = []
    labels = []

    for trial in all_trials:
        label = determine_outcome(trial)

        if label is not None:  # Skip trials without sufficient data
            trials.append(trial)
            labels.append(label)

    # Log labeling statistics
    logger.info("")
    log_labeling_report(all_trials)

    logger.info(f"\nUsable training data: {len(trials)} trials (labeled)")
    logger.info(f"Success: {sum(labels)} | Failure: {len(labels) - sum(labels)}")

    return trials, labels


def train_and_save_model(
    trials: list,
    labels: list,
    model_path: str = "models/outcome_model.json",
    schema_path: str = "models/feature_schema.json",
):
    """
    Train the outcome prediction model and save it with feature schema.

    Args:
        trials: List of ClinicalTrial objects
        labels: Binary labels (1=success, 0=failure)
        model_path: Path to save trained model
        schema_path: Path to save feature schema
    """
    logger.info("Training outcome prediction model...")

    # Initialize predictor with feature engineer
    predictor = OutcomePredictor(schema_path=None)  # Will create new schema

    # Train with validation split
    metrics = predictor.train(
        trials=trials,
        labels=labels,
        validation_split=0.2,
    )

    logger.info(f"Training metrics: {metrics}")

    # Save model
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    predictor.save(model_path)
    logger.info(f"✓ Model saved to {model_path}")

    # Save feature schema
    feature_importance = predictor.model.feature_importances_
    feature_importance_dict = dict(zip(predictor.feature_names, feature_importance))

    predictor.feature_engineer.save_schema(
        schema_path=schema_path,
        version="1.0.0",
        model_type="XGBoost",
        n_trials=len(trials),
        feature_importance=feature_importance_dict,
    )
    logger.info(f"✓ Feature schema saved to {schema_path}")

    return predictor, metrics


def save_test_set(
    test_trials: list,
    test_labels: list,
    test_set_path: str = "models/test_set.pkl",
    test_metadata_path: str = "models/test_set_metadata.json",
):
    """
    Save test set for benchmarking.

    Users can load this to test predictions on trials with known outcomes.

    Args:
        test_trials: List of test trials
        test_labels: Corresponding labels
        test_set_path: Path to save pickled test set
        test_metadata_path: Path to save test set metadata
    """
    logger.info("Saving test set for benchmarking...")

    # Save trials and labels as pickle
    test_data = {
        "trials": test_trials,
        "labels": test_labels,
    }

    Path(test_set_path).parent.mkdir(parents=True, exist_ok=True)
    with open(test_set_path, "wb") as f:
        pickle.dump(test_data, f)

    logger.info(f"✓ Test set saved to {test_set_path}")

    # Save metadata as JSON
    metadata = {
        "n_trials": len(test_trials),
        "n_success": sum(test_labels),
        "n_failure": len(test_labels) - sum(test_labels),
        "success_rate": sum(test_labels) / len(test_labels) if test_labels else 0,
        "trial_ids": [trial.nct_id for trial in test_trials],
        "created_at": datetime.now().isoformat(),
    }

    with open(test_metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"✓ Test metadata saved to {test_metadata_path}")
    logger.info(f"  - {metadata['n_trials']} trials ({metadata['success_rate']:.1%} success rate)")


def evaluate_model(predictor: OutcomePredictor, test_trials: list, test_labels: list):
    """
    Evaluate model performance on test set.

    Args:
        predictor: Trained model
        test_trials: Test trials
        test_labels: Test labels
    """
    logger.info("Evaluating model on test set...")

    predictions = []
    probabilities = []

    for trial in test_trials:
        result = predictor.predict(trial)
        probabilities.append(result.success_probability)
        predictions.append(1 if result.success_probability > 0.5 else 0)

    # Calculate metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

    accuracy = accuracy_score(test_labels, predictions)
    precision = precision_score(test_labels, predictions, zero_division=0)
    recall = recall_score(test_labels, predictions, zero_division=0)
    auc = roc_auc_score(test_labels, probabilities)

    logger.info("Test Set Metrics:")
    logger.info(f"  Accuracy:  {accuracy:.3f}")
    logger.info(f"  Precision: {precision:.3f}")
    logger.info(f"  Recall:    {recall:.3f}")
    logger.info(f"  AUC-ROC:   {auc:.3f}")

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "auc": auc,
    }


async def main():
    """Main training pipeline."""
    setup_logging()

    logger.info("="*80)
    logger.info("TrialSense AI - Model Training Pipeline")
    logger.info("="*80)

    # 1. Fetch training data
    logger.info("\n[1/4] Fetching training data...")
    trials, labels = await fetch_training_data(max_trials=500)

    if len(trials) < 50:
        logger.warning("Insufficient training data. Consider fetching more trials.")
        return

    # 2. Split into train/test
    logger.info("\n[2/4] Splitting data...")
    split_idx = int(len(trials) * 0.8)
    train_trials = trials[:split_idx]
    train_labels = labels[:split_idx]
    test_trials = trials[split_idx:]
    test_labels = labels[split_idx:]

    logger.info(f"  Train: {len(train_trials)} trials")
    logger.info(f"  Test:  {len(test_trials)} trials")

    # 3. Train model
    logger.info("\n[3/5] Training model...")
    predictor, train_metrics = train_and_save_model(
        trials=train_trials,
        labels=train_labels,
    )

    # 4. Save test set for benchmarking
    logger.info("\n[4/5] Saving test set for benchmarking...")
    save_test_set(test_trials, test_labels)

    # 5. Evaluate
    logger.info("\n[5/5] Evaluating model...")
    test_metrics = evaluate_model(predictor, test_trials, test_labels)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("Training Complete!")
    logger.info("="*80)
    logger.info(f"✓ Model saved to: models/outcome_model.json")
    logger.info(f"✓ Feature schema saved to: models/feature_schema.json")
    logger.info(f"✓ Test set saved to: models/test_set.pkl")
    logger.info(f"")
    logger.info(f"Training samples: {len(train_trials)}")
    logger.info(f"Test samples: {len(test_trials)}")
    logger.info(f"Test AUC: {test_metrics['auc']:.3f}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"")
    logger.info(f"Users can now benchmark predictions using the test set:")
    logger.info(f"  python scripts/benchmark_model.py")


if __name__ == "__main__":
    asyncio.run(main())
