#!/usr/bin/env python
"""
Benchmark model predictions on the test set.

This script loads the saved test set and evaluates model predictions
on trials with known outcomes. Useful for:
- Validating model performance
- Testing changes to the prediction pipeline
- Demonstrating prediction accuracy to stakeholders
"""

import pickle
import json
from pathlib import Path

from trialsense.models.outcome_predictor import OutcomePredictor
from trialsense.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def load_test_set(test_set_path: str = "models/test_set.pkl"):
    """Load the saved test set."""
    logger.info(f"Loading test set from {test_set_path}...")

    if not Path(test_set_path).exists():
        raise FileNotFoundError(
            f"Test set not found at {test_set_path}. "
            f"Run 'python scripts/train_model.py' first to create it."
        )

    with open(test_set_path, "rb") as f:
        test_data = pickle.load(f)

    trials = test_data["trials"]
    labels = test_data["labels"]

    logger.info(f"✓ Loaded {len(trials)} trials from test set")
    return trials, labels


def benchmark_predictions(
    predictor: OutcomePredictor,
    test_trials: list,
    test_labels: list,
    show_details: bool = False,
):
    """
    Benchmark model predictions on test set.

    Args:
        predictor: Trained model
        test_trials: Test trials with known outcomes
        test_labels: True labels (1=success, 0=failure)
        show_details: If True, show per-trial predictions
    """
    logger.info("Running predictions on test set...")

    predictions = []
    probabilities = []
    results = []

    for i, (trial, true_label) in enumerate(zip(test_trials, test_labels)):
        # Make prediction
        result = predictor.predict(trial)

        # Store results
        proba = result.success_probability
        pred_label = 1 if proba > 0.5 else 0

        probabilities.append(proba)
        predictions.append(pred_label)

        results.append({
            "nct_id": trial.nct_id,
            "title": trial.title,
            "true_label": true_label,
            "predicted_proba": proba,
            "predicted_label": pred_label,
            "correct": pred_label == true_label,
            "risk_factors": result.risk_factors,
            "positive_factors": result.positive_factors,
        })

        # Show details if requested
        if show_details:
            status = "✓" if pred_label == true_label else "✗"
            logger.info(
                f"  {status} {trial.nct_id}: "
                f"Pred={proba:.2f} (True={true_label})"
            )

    # Calculate metrics
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        roc_auc_score,
        confusion_matrix,
    )

    accuracy = accuracy_score(test_labels, predictions)
    precision = precision_score(test_labels, predictions, zero_division=0)
    recall = recall_score(test_labels, predictions, zero_division=0)
    auc = roc_auc_score(test_labels, probabilities)
    cm = confusion_matrix(test_labels, predictions)

    # Print results
    logger.info("\n" + "="*60)
    logger.info("Benchmark Results")
    logger.info("="*60)
    logger.info(f"Test Trials:  {len(test_trials)}")
    logger.info(f"")
    logger.info(f"Accuracy:     {accuracy:.3f} ({int(accuracy*len(test_trials))}/{len(test_trials)} correct)")
    logger.info(f"Precision:    {precision:.3f}")
    logger.info(f"Recall:       {recall:.3f}")
    logger.info(f"AUC-ROC:      {auc:.3f}")
    logger.info(f"")
    logger.info("Confusion Matrix:")
    logger.info(f"                 Predicted")
    logger.info(f"                 Fail  Success")
    logger.info(f"  Actual  Fail    {cm[0][0]:3d}    {cm[0][1]:3d}")
    logger.info(f"        Success   {cm[1][0]:3d}    {cm[1][1]:3d}")
    logger.info("="*60)

    # Show misclassifications
    misclassified = [r for r in results if not r["correct"]]
    if misclassified:
        logger.info(f"\nMisclassified Trials ({len(misclassified)}):")
        for r in misclassified[:5]:  # Show first 5
            logger.info(f"  {r['nct_id']}: Predicted {r['predicted_proba']:.2f}, Actual {r['true_label']}")
            logger.info(f"    Title: {r['title'][:60]}...")

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "auc": auc,
        "confusion_matrix": cm.tolist(),
        "results": results,
    }


def main():
    """Main benchmarking pipeline."""
    setup_logging()

    logger.info("="*60)
    logger.info("TrialSense AI - Model Benchmarking")
    logger.info("="*60)

    # Check if model exists
    model_path = "models/outcome_model.json"
    schema_path = "models/feature_schema.json"

    if not Path(model_path).exists():
        logger.error(f"Model not found at {model_path}")
        logger.error("Run 'python scripts/train_model.py' first")
        return

    # Load model
    logger.info(f"\nLoading model from {model_path}...")
    predictor = OutcomePredictor(
        model_path=model_path,
        schema_path=schema_path if Path(schema_path).exists() else None,
    )

    # Load test set
    logger.info("")
    test_trials, test_labels = load_test_set()

    # Load metadata
    metadata_path = "models/test_set_metadata.json"
    if Path(metadata_path).exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
        logger.info(f"Test set created: {metadata['created_at']}")
        logger.info(f"Success rate: {metadata['success_rate']:.1%}")

    # Run benchmark
    logger.info("")
    metrics = benchmark_predictions(
        predictor,
        test_trials,
        test_labels,
        show_details=False,  # Set to True to see per-trial predictions
    )

    # Save results
    results_path = "models/benchmark_results.json"
    with open(results_path, "w") as f:
        # Convert results to JSON-serializable format
        json_metrics = {
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "auc": metrics["auc"],
            "confusion_matrix": metrics["confusion_matrix"],
            "n_trials": len(test_trials),
            "benchmarked_at": json.dumps({"timestamp": "now"}),  # Placeholder
        }
        json.dump(json_metrics, f, indent=2)

    logger.info(f"\n✓ Results saved to {results_path}")


if __name__ == "__main__":
    main()
