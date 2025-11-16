# Example Trial Upload Files

This directory contains example JSON files demonstrating how to upload new trial protocols for outcome prediction.

## Files

### `trial_upload_complete.json`
**Complete trial protocol** with all recommended fields populated.

- Use this as a template for comprehensive trial uploads
- Includes: phase, enrollment, sponsor, conditions, interventions, locations, eligibility criteria, outcomes
- This format will typically provide immediate predictions without additional prompting

**Use case:** You have a fully designed protocol and want immediate prediction

### `trial_upload_minimal.json`
**Minimal trial protocol** with only essential fields.

- Demonstrates the minimum required information
- Missing fields (e.g., allocation, masking, locations, sponsor details) will trigger interactive prompts
- Shows how the system handles incomplete data

**Use case:** You're in early design phase and want to iteratively explore predictions as you fill in details

## How to Use

### Option 1: Streamlit UI

```bash
streamlit run trialsense/app/streamlit_app.py
```

1. Select "Upload trial protocol (new trial)"
2. Upload one of these JSON files
3. If missing features are detected, you'll be prompted to provide them
4. Once complete, prediction will be generated

### Option 2: Python API

```python
from trialsense.models.outcome_predictor import OutcomePredictor
from trialsense.data.trial_parser import TrialParser
import json

# Load trial data
with open("examples/trial_upload_complete.json") as f:
    trial_data = json.load(f)

# Parse and predict
parser = TrialParser()
trial_dict = parser.parse_json(trial_data)

predictor = OutcomePredictor(
    model_path="models/outcome_model.json",
    schema_path="models/feature_schema.json"
)

# Check for missing features
missing, prompts = predictor.get_missing_features(trial_dict)

if missing:
    print(f"Missing features: {missing}")
    print("Prompts:", prompts)

    # Collect user inputs...
    user_inputs = {}  # Fill with user-provided values

    # Predict with user inputs
    result = predictor.predict(trial_dict, user_inputs=user_inputs)
else:
    # Predict directly
    result = predictor.predict(trial_dict)

print(f"Success probability: {result.success_probability:.1%}")
print(f"Risk factors: {result.risk_factors}")
print(f"Positive factors: {result.positive_factors}")
```

### Option 3: REST API

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d @examples/trial_upload_complete.json
```

## JSON Schema

### Required Fields

Minimum fields needed (system will prompt for others):

```json
{
  "title": "string",
  "phase": "PHASE_1 | PHASE_2 | PHASE_3 | PHASE_4",
  "enrollment": number,
  "conditions": [{"name": "string"}]
}
```

### Recommended Fields

For best predictions without prompting:

```json
{
  "title": "string",
  "phase": "string",
  "enrollment": number,
  "study_type": "INTERVENTIONAL | OBSERVATIONAL",
  "allocation": "RANDOMIZED | NON_RANDOMIZED",
  "masking": "NONE | SINGLE | DOUBLE | TRIPLE",
  "sponsor": {
    "name": "string",
    "type": "INDUSTRY | ACADEMIC | GOVERNMENT"
  },
  "conditions": [{"name": "string"}],
  "interventions": [{"type": "DRUG | DEVICE | ...", "name": "string"}],
  "locations": [{"facility": "string", "city": "string", "state": "string"}],
  "eligibility_criteria": "string",
  "minimum_age": "string",
  "maximum_age": "string"
}
```

### Full Fields

See `trial_upload_complete.json` for all supported fields.

## Features Extracted

The system automatically extracts these features from your upload:

1. **Phase Features:** phase_numeric (1-5)
2. **Enrollment Features:** enrollment, enrollment_log
3. **Sponsor Features:** sponsor_type, has_collaborators, num_collaborators
4. **Design Features:** is_randomized, is_blinded, is_interventional
5. **Complexity Features:** num_conditions, num_interventions, num_locations, num_secondary_outcomes
6. **Eligibility Features:** has_age_restriction, criteria_length
7. **Site Features:** is_multicenter
8. **Therapeutic Area:** therapeutic_area (primary condition)

**Total: 17 features** used by the prediction model.

## Interactive Prompting Example

If you upload `trial_upload_minimal.json`, you'll be prompted for:

- **Allocation:** "Is this a randomized trial?" → [Yes/No]
- **Masking:** "Is this trial blinded/masked?" → [None/Single/Double/Triple]
- **Sponsor Type:** "What type of sponsor?" → [Industry/Academic/Government]
- **Number of Sites:** "How many trial sites/locations planned?" → [number]
- **Etc.**

The system will explain why each feature is important and provide sensible defaults where applicable.

## Tips

1. **Start minimal, iterate:** Upload minimal JSON, see what's missing, add fields incrementally
2. **Check prompts:** Use `get_missing_features()` to see what will be asked before uploading
3. **Save templates:** Create JSON templates for different trial types (Phase 1, Phase 3, etc.)
4. **Validate first:** Use the parser to validate your JSON before prediction:

```python
parser = TrialParser()
is_valid, errors = parser.validate_upload(trial_data)
if not is_valid:
    print("Errors:", errors)
```

## Comparison: Existing vs New Trials

| Workflow | Input | Feature Extraction | Prompting |
|----------|-------|-------------------|-----------|
| **Existing Trial** | NCT ID (e.g., "NCT04567890") | Automatic from API | Rare (data usually complete) |
| **New Trial** | JSON upload | Partial (from upload) | Common (many fields missing) |

Both workflows use the **same pre-trained model** for prediction.

## Next Steps

After getting a prediction:

1. **Review risk factors:** Understand what might affect success
2. **Optimize design:** Modify trial parameters based on insights
3. **Re-predict:** Upload updated JSON to see how changes affect probability
4. **Compare designs:** Upload multiple variants to find optimal design

---

**Questions?** See [docs/predictive_modeling_workflow.md](../docs/predictive_modeling_workflow.md) for detailed workflow documentation.
