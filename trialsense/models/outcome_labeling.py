"""
Outcome labeling for clinical trial success prediction.

This module defines how we label trials as success/failure for ML training.

IMPORTANT: This is Phase 2 (Improved) labeling.
- Uses trial status + has_results + termination reasons
- Does NOT parse actual primary outcome p-values
- See docs/target_variable_definition.md for details

Limitations:
- has_results is a proxy (not all positive trials submit results)
- Doesn't distinguish statistical significance
- Termination reason keywords may miss nuances

Future work (Phase 3):
- Parse primary outcome XML for p-values
- Cross-reference with FDA approvals
- Validate against published literature
"""

from datetime import datetime, timedelta
from typing import Optional
from trialsense.data.models import ClinicalTrial, TrialStatus
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


# Type aliases
OutcomeLabel = Optional[int]  # 0 = failure, 1 = success, None = skip


def determine_outcome(trial: ClinicalTrial) -> OutcomeLabel:
    """
    Label trial outcome for ML training (Phase 2: Improved labeling).

    Success criteria:
    1. Status is COMPLETED and has_results=True, OR
    2. Status is TERMINATED but reason indicates early success

    Failure criteria:
    1. Status is TERMINATED/WITHDRAWN (except early success), OR
    2. Status is COMPLETED but no results after 2+ years

    Skip criteria (return None):
    1. Status is RECRUITING, ACTIVE, etc. (not finished)
    2. Status is COMPLETED but too recent (<2 years, no results yet)

    Args:
        trial: ClinicalTrial object

    Returns:
        1 = success
        0 = failure
        None = skip (insufficient data)

    Example:
        >>> trial = ClinicalTrial(status=TrialStatus.COMPLETED, has_results=True)
        >>> determine_outcome(trial)
        1

        >>> trial = ClinicalTrial(status=TrialStatus.TERMINATED, why_stopped="Lack of enrollment")
        >>> determine_outcome(trial)
        0
    """
    # === TERMINATED TRIALS ===
    if trial.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN, TrialStatus.SUSPENDED]:
        return _label_terminated_trial(trial)

    # === COMPLETED TRIALS ===
    if trial.status == TrialStatus.COMPLETED:
        return _label_completed_trial(trial)

    # === OTHER STATUSES (RECRUITING, ACTIVE, ETC.) ===
    # Skip trials that haven't finished yet
    logger.debug(f"Skipping {trial.nct_id}: status={trial.status} (not finished)")
    return None


def _label_terminated_trial(trial: ClinicalTrial) -> OutcomeLabel:
    """
    Label a terminated/withdrawn/suspended trial.

    Most terminations are failures, but some indicate early success
    (e.g., "trial met endpoints at interim analysis").

    Args:
        trial: Terminated trial

    Returns:
        1 if early success, 0 if failure
    """
    # Check termination reason
    if trial.why_stopped:
        why_lower = trial.why_stopped.lower()

        # Early success keywords
        early_success_keywords = [
            "met endpoint",
            "met primary endpoint",
            "positive interim",
            "overwhelming efficacy",
            "success",
            "achieved endpoint early",
            "superiority demonstrated",
        ]

        if any(kw in why_lower for kw in early_success_keywords):
            logger.info(
                f"{trial.nct_id}: Terminated early due to SUCCESS - {trial.why_stopped}"
            )
            return 1  # Early success

    # All other terminations are failures
    logger.debug(
        f"{trial.nct_id}: Terminated (failure) - {trial.why_stopped or 'reason unknown'}"
    )
    return 0


def _label_completed_trial(trial: ClinicalTrial) -> OutcomeLabel:
    """
    Label a completed trial.

    Heuristic:
    - Has results → likely positive (success)
    - No results after 2+ years → likely negative (failure)
    - No results but <2 years → skip (too recent)

    Rationale:
    Trials with positive results are more likely to submit results to
    ClinicalTrials.gov. Negative results are often not submitted.

    Args:
        trial: Completed trial

    Returns:
        1 if has results, 0 if no results after 2 years, None if too recent
    """
    # Has results = likely positive
    if trial.has_results:
        logger.debug(f"{trial.nct_id}: Completed with results (success)")
        return 1

    # No results - check how long since completion
    if trial.completion_date:
        days_since_completion = (datetime.now().date() - trial.completion_date).days

        # No results after 2 years → likely negative
        if days_since_completion > 730:  # 2 years
            logger.debug(
                f"{trial.nct_id}: Completed {days_since_completion} days ago, "
                f"no results (likely failure)"
            )
            return 0

        # Too recent - results may still be forthcoming
        logger.debug(
            f"{trial.nct_id}: Completed {days_since_completion} days ago, "
            f"no results yet (skipping - too recent)"
        )
        return None

    # Completion date unknown - skip
    logger.debug(f"{trial.nct_id}: Completed but no completion_date (skipping)")
    return None


def determine_outcome_multiclass(trial: ClinicalTrial) -> Optional[int]:
    """
    Label trial with multi-class outcome (0-4).

    Classes:
    0: Safety termination (terminated due to adverse events)
    1: Efficacy termination (terminated due to futility/negative interim)
    2: Operational termination (enrollment, funding, sponsor decision)
    3: Completed but negative (primary endpoint likely not met)
    4: Completed and positive (primary endpoint likely met)

    Args:
        trial: ClinicalTrial object

    Returns:
        Class label (0-4) or None if should skip

    Example:
        >>> trial = ClinicalTrial(
        ...     status=TrialStatus.TERMINATED,
        ...     why_stopped="Safety concerns - increased adverse events"
        ... )
        >>> determine_outcome_multiclass(trial)
        0  # Safety termination
    """
    # === TERMINATED TRIALS ===
    if trial.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN, TrialStatus.SUSPENDED]:
        if not trial.why_stopped:
            return 2  # Unknown reason → operational

        why_lower = trial.why_stopped.lower()

        # Safety termination
        safety_keywords = [
            "safety",
            "adverse",
            "toxicity",
            "death",
            "serious adverse event",
            "unacceptable toxicity",
        ]
        if any(kw in why_lower for kw in safety_keywords):
            logger.debug(f"{trial.nct_id}: Safety termination")
            return 0

        # Efficacy termination (futility)
        futility_keywords = [
            "futility",
            "lack of efficacy",
            "negative interim",
            "unlikely to meet endpoint",
            "insufficient efficacy",
        ]
        if any(kw in why_lower for kw in futility_keywords):
            logger.debug(f"{trial.nct_id}: Efficacy/futility termination")
            return 1

        # Operational termination
        logger.debug(f"{trial.nct_id}: Operational termination - {trial.why_stopped}")
        return 2

    # === COMPLETED TRIALS ===
    if trial.status == TrialStatus.COMPLETED:
        if trial.has_results:
            logger.debug(f"{trial.nct_id}: Completed with results (positive)")
            return 4  # Completed and positive
        else:
            # Check time since completion
            if trial.completion_date:
                days_since = (datetime.now().date() - trial.completion_date).days
                if days_since > 730:
                    logger.debug(f"{trial.nct_id}: Completed, no results (negative)")
                    return 3  # Completed but negative
                else:
                    return None  # Too recent, skip

            return None  # No completion date, skip

    # === OTHER STATUSES ===
    return None  # Skip


def get_labeling_statistics(trials: list[ClinicalTrial]) -> dict:
    """
    Compute labeling statistics for a list of trials.

    Useful for understanding label distribution and data quality.

    Args:
        trials: List of ClinicalTrial objects

    Returns:
        Dictionary with counts and percentages

    Example:
        >>> trials = [...]  # 1000 trials
        >>> stats = get_labeling_statistics(trials)
        >>> print(stats)
        {
            'total_trials': 1000,
            'labeled': 650,
            'skipped': 350,
            'success': 380,
            'failure': 270,
            'success_rate': 0.585,
            ...
        }
    """
    total = len(trials)
    labels = [determine_outcome(t) for t in trials]

    success_count = sum(1 for l in labels if l == 1)
    failure_count = sum(1 for l in labels if l == 0)
    skipped_count = sum(1 for l in labels if l is None)
    labeled_count = success_count + failure_count

    # Termination breakdown
    terminated_trials = [
        t for t in trials
        if t.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN]
    ]
    early_success = sum(
        1 for t in terminated_trials
        if determine_outcome(t) == 1
    )

    return {
        "total_trials": total,
        "labeled": labeled_count,
        "skipped": skipped_count,
        "success": success_count,
        "failure": failure_count,
        "success_rate": success_count / labeled_count if labeled_count > 0 else 0,
        "termination_rate": len(terminated_trials) / total if total > 0 else 0,
        "early_success_rate": early_success / len(terminated_trials) if terminated_trials else 0,
        "labeling_coverage": labeled_count / total if total > 0 else 0,
    }


def log_labeling_report(trials: list[ClinicalTrial]) -> None:
    """
    Log a detailed labeling statistics report.

    Args:
        trials: List of trials to analyze
    """
    stats = get_labeling_statistics(trials)

    logger.info("="*60)
    logger.info("Outcome Labeling Statistics")
    logger.info("="*60)
    logger.info(f"Total trials:       {stats['total_trials']}")
    logger.info(f"Labeled:            {stats['labeled']} ({stats['labeling_coverage']:.1%})")
    logger.info(f"  ├─ Success:       {stats['success']} ({stats['success_rate']:.1%})")
    logger.info(f"  └─ Failure:       {stats['failure']} ({1-stats['success_rate']:.1%})")
    logger.info(f"Skipped:            {stats['skipped']}")
    logger.info(f"")
    logger.info(f"Termination rate:   {stats['termination_rate']:.1%}")
    logger.info(f"Early success rate: {stats['early_success_rate']:.1%} (of terminated)")
    logger.info("="*60)
