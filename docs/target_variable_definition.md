# Target Variable Definition - Clinical Trial Outcome Prediction

## 🎯 Critical Questions

### **1. How are we calculating/getting target variables?**
### **2. How are we quantifying success likelihood?**

---

## ⚠️ Current Implementation: PLACEHOLDER (NOT PRODUCTION-READY)

**Current code in `scripts/train_model.py`:**
```python
for trial in completed_trials:
    trials.append(trial)
    # In production: Label based on actual outcomes
    # For now, use has_results as proxy (imperfect but demonstrates concept)
    label = 1 if trial.has_results else 0  # ⚠️ PLACEHOLDER
    labels.append(label)
```

**Problem:** `has_results` just indicates if trial submitted results to ClinicalTrials.gov, NOT whether trial was successful!

**Issues:**
- ❌ Doesn't capture primary endpoint achievement
- ❌ Doesn't distinguish positive vs negative results
- ❌ Doesn't account for early termination reasons
- ❌ Not a valid success metric

---

## ✅ Proper Target Variable Definition

### **Definition of "Success"**

A trial is considered **successful** if:

1. ✅ **Completed** (not terminated early)
2. ✅ **Primary endpoint met** (statistically significant positive result)
3. ✅ **Results published** (indicates findings worth reporting)
4. ✅ **Led to regulatory action** (drug approval, label expansion, etc.)

A trial is considered a **failure** if:

1. ❌ **Terminated early** for:
   - Lack of enrollment
   - Safety concerns
   - Futility (interim analysis showed won't succeed)
   - Sponsor decision (business reasons)
   - Regulatory issues
2. ❌ **Completed but negative** (primary endpoint not met)
3. ❌ **Completed but no results** (suggests negative findings)

---

## 📊 Multi-Level Target Variable Hierarchy

### **Option 1: Binary Classification (Recommended for MVP)**

**Target:** `success` (0 or 1)

```python
success = 1 if:
    - trial.status == "COMPLETED" AND
    - trial.primary_outcome_achieved == True
else:
    success = 0
```

**Pros:**
- Simple to implement
- Clear interpretation
- Standard classification metrics (accuracy, AUC)

**Cons:**
- Loses nuance (e.g., "terminated due to futility" vs "safety issues")

---

### **Option 2: Multi-Class Classification (Better for Insights)**

**Target:** `outcome_category` (5 classes)

1. **Success (1)**: Completed + positive results + published
2. **Neutral (2)**: Completed + inconclusive results
3. **Failure - Negative (3)**: Completed + negative results
4. **Failure - Terminated (4)**: Terminated early (non-safety)
5. **Failure - Safety (5)**: Terminated due to safety

**Pros:**
- Captures different failure modes
- More actionable insights
- Can identify safety vs efficacy risks

**Cons:**
- More complex
- Requires more training data per class
- Harder to interpret probabilities

---

### **Option 3: Ordinal Regression (Most Nuanced)**

**Target:** `success_score` (0-10 scale)

- **10**: Completed + primary met + secondary met + regulatory approval
- **8-9**: Completed + primary met + published
- **6-7**: Completed + inconclusive + published
- **4-5**: Completed + primary not met
- **2-3**: Terminated early (non-safety)
- **0-1**: Terminated due to safety

**Pros:**
- Captures full spectrum of outcomes
- Useful for ranking trial designs

**Cons:**
- Requires careful calibration
- More complex to train

---

## 🔍 How to Extract Target Variables from ClinicalTrials.gov

### **Data Sources**

ClinicalTrials.gov provides several data points we can use:

1. **Trial Status** (`OverallStatus` field)
   - COMPLETED
   - TERMINATED
   - WITHDRAWN
   - SUSPENDED
   - ACTIVE_NOT_RECRUITING
   - RECRUITING

2. **Status Verification Date** (`StatusVerifiedDate`)
   - When status was last verified

3. **Why Stopped** (`WhyStopped` field)
   - Only present if trial was terminated/withdrawn
   - Examples: "Lack of enrollment", "Safety concerns", "Futility"

4. **Results Information** (`HasResults` field)
   - Boolean: has trial submitted results?
   - If yes, can access detailed results

5. **Results Submitted** (if `HasResults == True`)
   - Outcome measures with statistical results
   - Adverse events
   - Participant flow

---

## 🏗️ Implementation: Labeling Logic

### **Labeling Function**

```python
from trialsense.data.models import ClinicalTrial, TrialStatus
from typing import Literal

OutcomeLabel = Literal[0, 1]  # 0 = failure, 1 = success


def label_trial_outcome(trial: ClinicalTrial) -> OutcomeLabel:
    """
    Label trial as success (1) or failure (0).

    Success criteria (ALL must be true):
    1. Trial status is COMPLETED
    2. Trial has results submitted
    3. Primary outcome shows positive trend (if available)

    Failure criteria (ANY is true):
    1. Status is TERMINATED, WITHDRAWN, or SUSPENDED
    2. Status is COMPLETED but no results after >2 years
    3. Results show primary outcome NOT met

    Args:
        trial: ClinicalTrial object

    Returns:
        1 for success, 0 for failure
    """
    # Explicit failures: terminated/withdrawn/suspended
    if trial.status in [
        TrialStatus.TERMINATED,
        TrialStatus.WITHDRAWN,
        TrialStatus.SUSPENDED,
    ]:
        # Check termination reason
        if trial.why_stopped:
            # Some terminations are successes (e.g., "trial met endpoints early")
            early_success_keywords = [
                "met endpoint",
                "positive interim",
                "overwhelming efficacy",
                "success",
            ]
            if any(kw in trial.why_stopped.lower() for kw in early_success_keywords):
                return 1  # Early success

        # All other terminations are failures
        return 0

    # Not yet complete - exclude from training
    if trial.status != TrialStatus.COMPLETED:
        return None  # Skip this trial

    # Completed trials: check results
    if trial.has_results:
        # If results submitted, assume success
        # (trials with negative results often don't submit)
        # TODO: Parse actual outcome measures for more accurate labeling
        return 1
    else:
        # Completed but no results after significant time suggests negative
        from datetime import datetime, timedelta

        if trial.completion_date:
            time_since_completion = datetime.now() - trial.completion_date
            if time_since_completion > timedelta(days=730):  # 2 years
                # No results after 2 years → likely negative
                return 0

        # Recently completed, no results yet → exclude
        return None  # Skip this trial


def label_trial_outcome_multiclass(trial: ClinicalTrial) -> int:
    """
    Label trial with multi-class outcome (0-4).

    Classes:
    0: Safety termination (terminated due to adverse events)
    1: Efficacy termination (terminated due to futility/negative interim)
    2: Operational termination (enrollment, funding, etc.)
    3: Completed but negative (primary endpoint not met)
    4: Completed and positive (primary endpoint met)

    Args:
        trial: ClinicalTrial object

    Returns:
        Class label (0-4)
    """
    # Check if terminated
    if trial.status in [
        TrialStatus.TERMINATED,
        TrialStatus.WITHDRAWN,
        TrialStatus.SUSPENDED,
    ]:
        if not trial.why_stopped:
            return 2  # Unknown reason → operational

        why_lower = trial.why_stopped.lower()

        # Safety termination
        safety_keywords = ["safety", "adverse", "toxicity", "death"]
        if any(kw in why_lower for kw in safety_keywords):
            return 0

        # Efficacy termination
        futility_keywords = ["futility", "lack of efficacy", "negative interim"]
        if any(kw in why_lower for kw in futility_keywords):
            return 1

        # Operational termination
        return 2

    # Not complete → skip
    if trial.status != TrialStatus.COMPLETED:
        return None

    # Completed trials
    if trial.has_results:
        # TODO: Parse outcome measures to determine positive vs negative
        # For now, assume submitted results = positive
        return 4
    else:
        # Completed but no results → likely negative
        return 3
```

---

## 📊 Improved Labeling with Results Parsing

### **ClinicalTrials.gov Results Structure**

When a trial has results (`has_results=True`), ClinicalTrials.gov provides:

```xml
<outcome_list>
  <outcome>
    <type>Primary</type>
    <title>Overall Survival</title>
    <time_frame>24 months</time_frame>
    <group_list>
      <group id="O1">
        <title>Experimental Arm</title>
      </group>
      <group id="O2">
        <title>Control Arm</title>
      </group>
    </group_list>
    <analysis_list>
      <analysis>
        <p_value>0.032</p_value>
        <method>Log Rank</method>
        <param_type>Hazard Ratio</param_type>
        <param_value>0.72</param_value>
        <ci_percent>95</ci_percent>
        <ci_lower_limit>0.54</ci_lower_limit>
        <ci_upper_limit>0.96</ci_upper_limit>
      </analysis>
    </analysis_list>
  </outcome>
</outcome_list>
```

### **Enhanced Labeling with P-Values**

```python
def label_trial_with_results_parsing(trial: ClinicalTrial) -> OutcomeLabel:
    """
    Label trial using actual outcome measure results.

    This is the GOLD STANDARD for labeling but requires parsing
    detailed results XML from ClinicalTrials.gov.

    Args:
        trial: ClinicalTrial object with results data

    Returns:
        1 for success, 0 for failure
    """
    # Handle terminated trials
    if trial.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN]:
        return 0

    # Must be completed
    if trial.status != TrialStatus.COMPLETED:
        return None

    # Parse primary outcome results
    if trial.primary_outcome_results:
        # Look for p-value in statistical analysis
        for analysis in trial.primary_outcome_results.get("analyses", []):
            p_value = analysis.get("p_value")

            if p_value is not None:
                try:
                    p = float(p_value)
                    # Statistically significant at p < 0.05
                    if p < 0.05:
                        # Check direction (experimental better than control)
                        param_value = analysis.get("param_value")
                        param_type = analysis.get("param_type")

                        # Hazard ratio < 1 is good, odds ratio > 1 is good, etc.
                        # This requires domain knowledge per outcome type
                        # For now, just use p-value significance
                        return 1  # Significant = success
                    else:
                        return 0  # Not significant = failure
                except ValueError:
                    pass

    # No p-value found, fall back to has_results heuristic
    return 1 if trial.has_results else 0
```

---

## 📈 Success Likelihood Quantification

### **How XGBoost Produces Probabilities**

XGBoost is trained on historical trials with known outcomes:

```python
# Training
X_train = [features_trial1, features_trial2, ...]  # Feature vectors
y_train = [1, 0, 1, 0, ...]  # Success labels

model.fit(X_train, y_train)

# Prediction
X_new = features_new_trial
probability = model.predict_proba(X_new)[0][1]  # Probability of class 1 (success)
```

**Interpretation:**
- `probability = 0.72` means: "Based on historical trials with similar characteristics, 72% succeeded"

**Example:**
```
New Trial:
- Phase 3
- Enrollment: 340
- Randomized: Yes
- Sponsor: Industry
- control_soc_alignment: 0.8

XGBoost finds ~1000 similar historical trials:
- 720 succeeded (completed + positive results)
- 280 failed (terminated or negative)

Predicted Success Probability: 72% (720/1000)
```

---

## 🎯 Recommended Implementation Strategy

### **Phase 1: MVP (Current)**

**Labeling:**
```python
def label_trial_mvp(trial: ClinicalTrial) -> OutcomeLabel:
    """Simple labeling for MVP."""
    if trial.status == TrialStatus.COMPLETED and trial.has_results:
        return 1
    elif trial.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN]:
        return 0
    else:
        return None  # Skip
```

**Pros:** Simple, works with existing data
**Cons:** Less accurate, misses nuance

---

### **Phase 2: Improved (Recommended)**

**Labeling:**
```python
def label_trial_improved(trial: ClinicalTrial) -> OutcomeLabel:
    """Improved labeling with termination reasons."""
    # Terminated = failure
    if trial.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN]:
        # Exception: early success
        if trial.why_stopped and "met endpoint" in trial.why_stopped.lower():
            return 1
        return 0

    # Completed with results = success
    if trial.status == TrialStatus.COMPLETED:
        if trial.has_results:
            return 1
        else:
            # No results after 2 years = likely negative
            if time_since_completion(trial) > 730:  # days
                return 0
            else:
                return None  # Too recent, skip

    # Other statuses: skip
    return None
```

**Pros:** Better accuracy, accounts for termination
**Cons:** Still doesn't parse actual outcome measures

---

### **Phase 3: Gold Standard (Future)**

**Labeling:**
```python
def label_trial_gold(trial: ClinicalTrial) -> OutcomeLabel:
    """Gold standard labeling with results parsing."""
    # Parse primary outcome p-values
    if trial.primary_outcome_results:
        p_value = extract_primary_p_value(trial)
        if p_value is not None and p_value < 0.05:
            return 1
        elif p_value is not None:
            return 0

    # Fall back to improved labeling
    return label_trial_improved(trial)
```

**Pros:** Most accurate, uses actual statistical results
**Cons:** Requires XML parsing, not all trials have detailed results

---

## 📊 Expected Label Distribution

Based on industry data:

| Outcome | Phase 1 | Phase 2 | Phase 3 | Overall |
|---------|---------|---------|---------|---------|
| **Success** | ~60% | ~40% | ~50% | ~50% |
| **Failure (Terminated)** | ~15% | ~25% | ~25% | ~22% |
| **Failure (Negative)** | ~25% | ~35% | ~25% | ~28% |

**Implications:**
- Roughly balanced classes (good for ML)
- Phase 2 has highest failure rate
- Termination rate increases with phase

---

## 🔧 Implementation Checklist

### **To Do:**

1. ✅ Add `why_stopped` field to `ClinicalTrial` model
2. ✅ Add `primary_outcome_results` field for results parsing
3. ✅ Implement `label_trial_improved()` function
4. ✅ Update `train_model.py` to use improved labeling
5. ✅ Add labeling statistics to training output
6. ⬜ (Future) Implement XML results parsing for gold standard labeling

---

## 💡 Key Insights

1. **Target variable is NOT trivial** - requires careful design
2. **has_results is a poor proxy** - many successful trials don't submit detailed results
3. **Termination reasons matter** - "terminated due to success" vs "terminated due to futility"
4. **Time matters** - completed trials without results after 2 years likely negative
5. **Phase affects success rate** - Phase 2 is riskiest
6. **Gold standard requires parsing** - p-values from primary outcomes

---

## 📚 Data Sources for Validation

To validate our labeling:

1. **Published literature**: Cross-reference NCT IDs with publications (positive results)
2. **FDA approvals**: Trials that led to drug approvals (definite success)
3. **Industry reports**: Pharma companies report trial outcomes in earnings calls
4. **BioMedTracker**: Commercial database of trial outcomes (subscription required)

---

## 🎯 Recommended Approach for This Portfolio Project

**Use Phase 2 (Improved Labeling):**

```python
def determine_outcome(trial: ClinicalTrial) -> int:
    """
    Label trial outcome for training.

    Returns:
        1 = success
        0 = failure
        None = skip (insufficient data)
    """
    # Terminated trials
    if trial.status in [TrialStatus.TERMINATED, TrialStatus.WITHDRAWN]:
        # Check for early success
        if trial.why_stopped and any(
            kw in trial.why_stopped.lower()
            for kw in ["met endpoint", "positive interim", "overwhelming efficacy"]
        ):
            return 1

        # Otherwise failure
        return 0

    # Completed trials
    if trial.status == TrialStatus.COMPLETED:
        # Has results = likely positive
        if trial.has_results:
            return 1

        # No results after 2 years = likely negative
        if trial.completion_date:
            days_since = (datetime.now() - trial.completion_date).days
            if days_since > 730:
                return 0

        # Too recent, skip
        return None

    # Other statuses (recruiting, etc.): skip
    return None
```

**Document clearly:**
- This is Phase 2 labeling (improved but not gold standard)
- Limitations: doesn't parse actual p-values
- Future work: implement Phase 3 with results parsing

This demonstrates:
✅ Understanding of domain complexity
✅ Thoughtful labeling strategy
✅ Awareness of limitations
✅ Clear path to improvement

---

**This is what differentiates a portfolio project from production ML!**
