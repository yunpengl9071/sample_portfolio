# Predictive Modeling Workflow - Complete Design

## 🎯 Overview

The predictive modeling system supports **two distinct workflows**:

1. **Existing Trial Analysis**: User provides NCT ID → fetch data → predict
2. **New Trial Design**: User uploads protocol → interactive feature engineering → predict

Both workflows use the **same pre-trained model** trained on all available historical trials.

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ TRAINING PHASE (One-Time, Offline)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Fetch ALL completed trials from ClinicalTrials.gov         │
│     ├─ COMPLETED status only (have outcomes)                   │
│     ├─ 50,000+ trials recommended                              │
│     └─ Takes: 1-3 hours                                        │
│                                                                 │
│  2. Engineer features from complete trial records              │
│     ├─ Extract: phase, enrollment, design, sponsor, etc.       │
│     ├─ Create derived features: log(enrollment), complexity    │
│     └─ Takes: 5-10 minutes                                     │
│                                                                 │
│  3. Label trials (success vs failure)                          │
│     ├─ Success: Completed with positive results               │
│     ├─ Failure: Terminated, suspended, or negative results    │
│     └─ Takes: 1 minute                                         │
│                                                                 │
│  4. Train XGBoost model                                        │
│     ├─ 80/20 train/validation split                           │
│     ├─ Hyperparameter tuning                                   │
│     └─ Takes: 10-30 minutes                                    │
│                                                                 │
│  5. Save model + feature schema                                │
│     ├─ models/outcome_model.json (XGBoost model)              │
│     ├─ models/feature_schema.json (required features)         │
│     └─ models/feature_statistics.json (for normalization)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ INFERENCE PHASE (Real-Time, Per User Query)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input: NCT ID OR Trial Protocol Upload                   │
│       │                                                         │
│       ├──────────────────┬──────────────────────────────────┐  │
│       │                  │                                  │  │
│   Path A:            Path B:                                │  │
│   Existing Trial     New Trial Design                       │  │
│       │                  │                                  │  │
│       ▼                  ▼                                  │  │
│  Fetch from API     Parse Upload                           │  │
│  (ClinicalTrials    (JSON/Form/                            │  │
│   .gov)             File)                                  │  │
│       │                  │                                  │  │
│       └──────────────────┴──────────────────────────────────┤  │
│                          │                                  │  │
│                          ▼                                  │  │
│              ┌────────────────────────┐                     │  │
│              │ Feature Engineering    │                     │  │
│              │ Module                 │                     │  │
│              └────────────────────────┘                     │  │
│                          │                                  │  │
│                          ├─ Extract features                │  │
│                          ├─ Validate completeness           │  │
│                          └─ Identify missing features       │  │
│                          │                                  │  │
│              ┌───────────┴───────────┐                      │  │
│              │                       │                      │  │
│          Complete?               Missing?                   │  │
│              │                       │                      │  │
│              │                       ▼                      │  │
│              │          ┌─────────────────────────┐         │  │
│              │          │ Prompt User for Missing │         │  │
│              │          │ Information             │         │  │
│              │          └─────────────────────────┘         │  │
│              │                       │                      │  │
│              │          ┌─────────────────────────┐         │  │
│              │          │ Examples:               │         │  │
│              │          │ "What is the enrollment │         │  │
│              │          │  target?"               │         │  │
│              │          │ "Select trial phase"    │         │  │
│              │          │ "Sponsor type?"         │         │  │
│              │          └─────────────────────────┘         │  │
│              │                       │                      │  │
│              │                       ▼                      │  │
│              │              User Provides Info             │  │
│              │                       │                      │  │
│              └───────────────────────┘                      │  │
│                          │                                  │  │
│                          ▼                                  │  │
│              ┌────────────────────────┐                     │  │
│              │ Complete Feature Vector│                     │  │
│              │ [17 engineered features]│                    │  │
│              └────────────────────────┘                     │  │
│                          │                                  │  │
│                          ▼                                  │  │
│              ┌────────────────────────┐                     │  │
│              │ XGBoost Prediction     │                     │  │
│              │ + SHAP Explanation     │                     │  │
│              └────────────────────────┘                     │  │
│                          │                                  │  │
│                          ▼                                  │  │
│              ┌────────────────────────┐                     │  │
│              │ Results:               │                     │  │
│              │ • Success probability  │                     │  │
│              │ • Confidence interval  │                     │  │
│              │ • Feature importance   │                     │  │
│              │ • Risk factors         │                     │  │
│              │ • Positive factors     │                     │  │
│              └────────────────────────┘                     │  │
│                                                             │  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Feature Engineering Details

### **Required Features (17 total)**

These are the features the model was trained on and MUST have for prediction:

**1. Phase Features (1)**
- `phase_numeric`: Encoded phase (1=Phase 1, 2=Phase 2, etc.)
  - Source: Direct from trial data
  - Prompt if missing: "What is the trial phase?" [dropdown: Phase 1, Phase 2, Phase 3, Phase 4]

**2. Enrollment Features (2)**
- `enrollment`: Target enrollment count
  - Source: Direct from trial data
  - Prompt if missing: "What is the target enrollment (number of participants)?"
- `enrollment_log`: log1p(enrollment) for better scaling
  - Derived from enrollment

**3. Sponsor Features (3)**
- `sponsor_type`: Industry, Academic, Government, etc.
  - Source: Direct from trial data
  - Prompt if missing: "What type of sponsor?" [dropdown: Industry, Academic, Government, Other]
- `has_collaborators`: Boolean (0 or 1)
  - Source: Check if collaborators list is non-empty
  - Prompt if missing: "Are there collaborating organizations?" [Yes/No]
- `num_collaborators`: Count of collaborators
  - Derived from collaborators list

**4. Study Design Features (3)**
- `is_randomized`: Boolean (0 or 1)
  - Source: allocation field
  - Prompt if missing: "Is this a randomized trial?" [Yes/No]
- `is_blinded`: Boolean (0 or 1)
  - Source: masking field
  - Prompt if missing: "Is this trial blinded/masked?" [dropdown: None, Single, Double, Triple]
- `is_interventional`: Boolean (0 or 1)
  - Source: study_type field
  - Prompt if missing: "Is this an interventional study?" [Yes/No - default Yes]

**5. Complexity Features (4)**
- `num_conditions`: Number of conditions being studied
  - Source: conditions list
  - Prompt if missing: "How many conditions/diseases are being studied?" [default: 1]
- `num_interventions`: Number of intervention arms
  - Source: interventions list
  - Prompt if missing: "How many intervention arms?" [required]
- `num_locations`: Number of trial sites
  - Source: locations list
  - Prompt if missing: "How many trial sites/locations planned?" [required]
- `num_secondary_outcomes`: Number of secondary endpoints
  - Source: secondary_outcomes list
  - Prompt if missing: "How many secondary outcome measures?" [default: 2]

**6. Eligibility Features (2)**
- `has_age_restriction`: Boolean (0 or 1)
  - Source: minimum_age or maximum_age fields
  - Prompt if missing: "Are there age restrictions?" [Yes/No]
- `criteria_length`: Length of eligibility criteria text
  - Source: eligibility_criteria string
  - Derived from inclusion/exclusion text length

**7. Site Features (1)**
- `is_multicenter`: Boolean (0 or 1)
  - Derived: 1 if num_locations > 1
  - Auto-computed from num_locations

**8. Therapeutic Area (1)**
- `therapeutic_area`: Primary condition category
  - Source: conditions[0].name
  - Prompt if missing: "Primary therapeutic area?" [dropdown or text]

---

## 📊 Feature Extraction Logic

### **Path A: Existing Trial (NCT ID provided)**

```python
# User provides: NCT04567890

# 1. Fetch from API
trial = await clinical_trials_client.get_trial("NCT04567890")

# 2. Extract features automatically
features = feature_engineer.extract_features(trial)

# 3. Check completeness
missing = feature_engineer.validate_features(features)

# If complete (typical for existing trials):
if not missing:
    prediction = outcome_predictor.predict(features)
    return prediction

# If missing (rare for existing trials):
else:
    # Prompt user for missing fields
    for field in missing:
        prompt_user(field)
    # Re-extract after user input
    features = feature_engineer.extract_features(trial, user_inputs)
    prediction = outcome_predictor.predict(features)
    return prediction
```

### **Path B: New Trial (Protocol upload)**

```python
# User provides: JSON/form data with trial design

# 1. Parse upload
trial_data = trial_parser.parse_upload(uploaded_file)

# 2. Extract features (many will be incomplete)
features = feature_engineer.extract_features_from_partial(trial_data)

# 3. Identify missing required features
missing = feature_engineer.validate_features(features)

# 4. Generate prompts for missing features
prompts = feature_engineer.generate_prompts(missing)

# 5. Present to user (interactive form)
"""
We need the following information to predict outcomes:

1. Trial Phase: [dropdown: Phase 1, Phase 2, Phase 3, Phase 4]
2. Target Enrollment: [number input]
3. Sponsor Type: [dropdown: Industry, Academic, Government, Other]
4. Number of Sites: [number input]
5. Number of Intervention Arms: [number input]
...
"""

# 6. User fills in missing info
user_inputs = get_user_inputs(prompts)

# 7. Re-extract with user inputs
features = feature_engineer.extract_features(trial_data, user_inputs)

# 8. Validate again (should be complete now)
if feature_engineer.validate_features(features):
    prediction = outcome_predictor.predict(features)
    return prediction
else:
    raise ValueError("Still missing required features")
```

---

## 🗂️ Upload Formats Supported

### **Option 1: JSON Upload**

```json
{
  "title": "A Phase 3 Study of Novel Immunotherapy in NSCLC",
  "phase": "PHASE_3",
  "enrollment": 340,
  "sponsor": {
    "name": "Acme Pharma",
    "type": "INDUSTRY"
  },
  "study_type": "INTERVENTIONAL",
  "allocation": "RANDOMIZED",
  "masking": "DOUBLE",
  "interventions": [
    {
      "type": "DRUG",
      "name": "Novel Immunotherapy",
      "description": "Experimental drug"
    },
    {
      "type": "DRUG",
      "name": "Placebo",
      "description": "Control"
    }
  ],
  "conditions": [
    {
      "name": "Non-Small Cell Lung Cancer"
    }
  ],
  "locations": [
    {
      "facility": "Johns Hopkins",
      "city": "Baltimore",
      "state": "MD",
      "country": "USA"
    }
  ],
  "eligibility_criteria": "Inclusion: Adults 18+, confirmed NSCLC...",
  "primary_outcome": {
    "measure": "Overall Survival",
    "time_frame": "24 months"
  },
  "secondary_outcomes": [
    {
      "measure": "Progression-Free Survival",
      "time_frame": "12 months"
    },
    {
      "measure": "Objective Response Rate",
      "time_frame": "6 months"
    }
  ],
  "minimum_age": "18 years",
  "collaborators": []
}
```

### **Option 2: Structured Form (Streamlit UI)**

```
┌─────────────────────────────────────────────────┐
│ Upload New Trial Protocol                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ Trial Title: [________________________________] │
│                                                 │
│ Phase: [▼ Phase 3                           ]  │
│                                                 │
│ Target Enrollment: [340]                        │
│                                                 │
│ Sponsor Type: [▼ Industry                   ]  │
│                                                 │
│ Study Type: [▼ Interventional               ]  │
│                                                 │
│ Allocation: [▼ Randomized                   ]  │
│                                                 │
│ Masking: [▼ Double Blind                    ]  │
│                                                 │
│ Number of Intervention Arms: [2]                │
│                                                 │
│ Number of Sites: [15]                           │
│                                                 │
│ Therapeutic Area: [Oncology - Lung Cancer]      │
│                                                 │
│ Inclusion/Exclusion Criteria:                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ Adults 18+                                  │ │
│ │ Confirmed NSCLC                             │ │
│ │ ECOG 0-1                                    │ │
│ │ No prior immunotherapy                      │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Age Restrictions: [✓] Yes                       │
│   Min Age: [18 years]                           │
│   Max Age: [80 years]                           │
│                                                 │
│ Collaborators: [___________________________]    │
│                                                 │
│ Secondary Outcomes (count): [2]                 │
│                                                 │
│  [Predict Outcome]                              │
│                                                 │
└─────────────────────────────────────────────────┘
```

### **Option 3: Text/PDF Parsing (Advanced)**

Upload protocol PDF → NLP extraction → prompt for missing fields

```python
# Extract from uploaded PDF
extracted = nlp_parser.parse_protocol_pdf(pdf_file)

# Example extracted fields:
{
    "phase": "Phase 3",  # extracted from text
    "enrollment": 340,   # extracted from "Sample size: 340"
    "allocation": None,  # NOT found in PDF → prompt user
    ...
}
```

---

## 🎨 User Interface Flow

### **Streamlit App - New Trial Upload**

```python
# Main UI
st.title("🧬 TrialSense AI - Outcome Prediction")

# Input method selector
input_method = st.radio(
    "How would you like to provide trial data?",
    [
        "📋 Enter NCT ID (existing trial)",
        "📄 Upload trial protocol (new trial)",
        "✍️ Fill out form (new trial)"
    ]
)

if input_method == "📋 Enter NCT ID (existing trial)":
    nct_id = st.text_input("Enter NCT ID:", "NCT04567890")
    if st.button("Predict Outcome"):
        # Path A: Fetch from API
        trial = fetch_trial(nct_id)
        features = extract_features(trial)
        prediction = predict(features)
        display_results(prediction)

elif input_method == "📄 Upload trial protocol (new trial)":
    uploaded_file = st.file_uploader("Upload JSON or PDF", type=["json", "pdf"])
    if uploaded_file:
        # Parse upload
        trial_data = parse_upload(uploaded_file)

        # Extract features
        features = extract_features_partial(trial_data)

        # Check for missing
        missing = validate_features(features)

        if missing:
            st.warning(f"⚠️ We need {len(missing)} additional pieces of information:")

            # Generate prompts dynamically
            user_inputs = {}
            for field in missing:
                user_inputs[field] = prompt_for_field(field)

            if st.button("Predict with Provided Info"):
                features.update(user_inputs)
                prediction = predict(features)
                display_results(prediction)

elif input_method == "✍️ Fill out form (new trial)":
    # Show comprehensive form
    with st.form("trial_form"):
        phase = st.selectbox("Phase", ["Phase 1", "Phase 2", "Phase 3", "Phase 4"])
        enrollment = st.number_input("Target Enrollment", min_value=1, value=100)
        sponsor_type = st.selectbox("Sponsor Type", ["Industry", "Academic", "Government"])
        # ... all other fields ...

        submitted = st.form_submit_button("Predict Outcome")
        if submitted:
            trial_data = create_trial_from_form(...)
            features = extract_features(trial_data)
            prediction = predict(features)
            display_results(prediction)
```

---

## 🔍 Feature Prompting Examples

### **Smart Prompting Based on Context**

```python
FEATURE_PROMPTS = {
    "phase_numeric": {
        "question": "What is the trial phase?",
        "type": "select",
        "options": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
        "required": True,
        "help": "The clinical trial phase determines the stage of drug development."
    },
    "enrollment": {
        "question": "What is the target enrollment (number of participants)?",
        "type": "number",
        "min": 1,
        "max": 100000,
        "required": True,
        "help": "Total number of participants you plan to enroll across all sites."
    },
    "sponsor_type": {
        "question": "What type of organization is sponsoring this trial?",
        "type": "select",
        "options": ["Industry", "Academic", "Government", "Other"],
        "required": True,
        "help": "Industry sponsors tend to have more resources but face different regulatory scrutiny."
    },
    "is_randomized": {
        "question": "Is this a randomized trial?",
        "type": "boolean",
        "default": True,
        "required": True,
        "help": "Randomization improves evidence quality and FDA approval likelihood."
    },
    "num_interventions": {
        "question": "How many intervention arms does this trial have?",
        "type": "number",
        "min": 1,
        "max": 10,
        "required": True,
        "help": "Including all treatment arms and control/placebo arms."
    },
    "num_locations": {
        "question": "How many trial sites/locations are planned?",
        "type": "number",
        "min": 1,
        "max": 1000,
        "required": True,
        "help": "Multi-site trials have higher recruitment potential but coordination complexity."
    },
    # ... all 17 features
}
```

---

## 📐 Feature Schema

### **Saved During Training**

```json
{
  "version": "1.0.0",
  "model_type": "XGBoost",
  "trained_on": "2025-01-15",
  "n_trials": 50000,
  "features": [
    {
      "name": "phase_numeric",
      "type": "categorical_encoded",
      "required": true,
      "encoding": {"PHASE_1": 2, "PHASE_2": 3, "PHASE_3": 4, "PHASE_4": 5},
      "default": null,
      "importance": 0.12
    },
    {
      "name": "enrollment",
      "type": "numeric",
      "required": true,
      "min": 1,
      "max": 50000,
      "mean": 215.4,
      "std": 450.2,
      "default": null,
      "importance": 0.18
    },
    {
      "name": "sponsor_type",
      "type": "categorical_encoded",
      "required": true,
      "encoding": {"INDUSTRY": 0, "ACADEMIC": 1, "GOVERNMENT": 2},
      "default": "INDUSTRY",
      "importance": 0.09
    }
    // ... all 17 features
  ],
  "feature_order": [
    "phase_numeric",
    "enrollment",
    "enrollment_log",
    "sponsor_type",
    "has_collaborators",
    "num_collaborators",
    "is_randomized",
    "is_blinded",
    "is_interventional",
    "num_conditions",
    "num_interventions",
    "num_locations",
    "num_secondary_outcomes",
    "has_age_restriction",
    "criteria_length",
    "is_multicenter",
    "therapeutic_area"
  ]
}
```

### **Loaded During Inference**

```python
class FeatureEngineer:
    def __init__(self, schema_path="models/feature_schema.json"):
        self.schema = self.load_schema(schema_path)
        self.required_features = [
            f["name"] for f in self.schema["features"] if f["required"]
        ]

    def validate_features(self, features: dict) -> list[str]:
        """Return list of missing required features."""
        missing = []
        for feature_name in self.required_features:
            if feature_name not in features or features[feature_name] is None:
                missing.append(feature_name)
        return missing

    def generate_prompt(self, feature_name: str) -> dict:
        """Generate UI prompt for a missing feature."""
        feature_def = self.schema["features"][feature_name]
        return {
            "question": FEATURE_PROMPTS[feature_name]["question"],
            "type": FEATURE_PROMPTS[feature_name]["type"],
            "help": FEATURE_PROMPTS[feature_name]["help"],
            ...
        }
```

---

## 🚀 Implementation Files

### **New Files to Create:**

1. **`trialsense/models/feature_engineer.py`**
   - `FeatureEngineer` class
   - `extract_features(trial)` - from ClinicalTrial object
   - `extract_features_partial(data)` - from partial upload
   - `validate_features(features)` - return missing list
   - `generate_prompts(missing)` - create UI prompts
   - `fill_defaults(features)` - apply defaults for optional features

2. **`trialsense/data/trial_parser.py`**
   - `TrialParser` class
   - `parse_json(json_data)` - parse JSON upload
   - `parse_form(form_data)` - parse Streamlit form
   - `parse_pdf(pdf_file)` - (future) NLP extraction from PDF
   - `create_trial_object(parsed_data)` - convert to ClinicalTrial

3. **`trialsense/models/feature_schema.py`**
   - `FeatureSchema` dataclass
   - `save_schema(features, path)` - save during training
   - `load_schema(path)` - load during inference

4. **`trialsense/app/components/trial_upload.py`**
   - Streamlit component for trial upload
   - `render_upload_ui()` - main upload interface
   - `render_missing_fields_form(missing)` - dynamic prompts

### **Files to Modify:**

1. **`trialsense/models/outcome_predictor.py`**
   - Update `predict()` to accept feature dict OR ClinicalTrial
   - Use `FeatureEngineer` instead of internal `_extract_features()`

2. **`trialsense/agents/outcome_agent.py`**
   - Support both existing trial and new trial paths
   - Handle missing feature prompting

3. **`trialsense/app/streamlit_app.py`**
   - Add upload UI
   - Add form UI
   - Add dynamic missing field prompting

4. **`scripts/train_model.py`**
   - Save feature schema during training
   - Save feature statistics (mean, std, etc.)

---

## 📊 Model Training Updates

### **Enhanced Training Script**

```python
# scripts/train_model.py

async def train_model():
    """Train model on ALL available trials and save feature schema."""

    # 1. Fetch ALL completed trials
    print("Fetching all completed trials...")
    trials = await fetch_all_completed_trials(
        min_trials=50000,
        statuses=["COMPLETED", "TERMINATED"]
    )

    # 2. Extract features using FeatureEngineer
    feature_engineer = FeatureEngineer()
    features_list = []
    labels = []

    for trial in trials:
        try:
            features = feature_engineer.extract_features(trial)
            label = determine_outcome(trial)  # 1=success, 0=failure
            features_list.append(features)
            labels.append(label)
        except Exception as e:
            print(f"Skipping trial {trial.nct_id}: {e}")

    # 3. Convert to numpy arrays
    X, feature_names = feature_engineer.to_numpy(features_list)
    y = np.array(labels)

    # 4. Train model
    model = OutcomePredictor()
    metrics = model.train(X, y, feature_names=feature_names)

    # 5. Save model
    model.save("models/outcome_model.json")

    # 6. Save feature schema
    feature_engineer.save_schema(
        "models/feature_schema.json",
        feature_importance=model.get_feature_importance()
    )

    # 7. Save feature statistics for normalization
    feature_engineer.save_statistics(
        "models/feature_statistics.json",
        X=X
    )

    print(f"✅ Model trained on {len(trials)} trials")
    print(f"✅ Metrics: {metrics}")
    print(f"✅ Saved: outcome_model.json, feature_schema.json")
```

---

## 🎯 Key Benefits

### **For Users:**
✅ **Flexibility**: Analyze both existing and new trials
✅ **Guidance**: Clear prompts for required information
✅ **Speed**: Existing trials auto-populate most features
✅ **Transparency**: Know exactly what the model needs

### **For Developers:**
✅ **Maintainability**: Single feature schema drives training + inference
✅ **Extensibility**: Easy to add new features
✅ **Validation**: Automatic checking of feature completeness
✅ **Debugging**: Clear error messages for missing features

### **For Production:**
✅ **Robustness**: Handles partial data gracefully
✅ **User Experience**: Interactive prompting vs hard errors
✅ **Model Versioning**: Feature schema tracks model version
✅ **Backwards Compatibility**: Can detect schema mismatches

---

## 📋 Summary

**Training (One-Time):**
- Fetch ALL completed trials (50k+)
- Engineer features from complete records
- Train XGBoost model
- Save model + feature schema + statistics

**Inference (Real-Time):**

**Path A (Existing Trial):**
- User provides NCT ID
- Fetch from API
- Auto-extract features
- Predict immediately (usually complete)

**Path B (New Trial):**
- User uploads protocol (JSON/form/PDF)
- Parse protocol
- Extract partial features
- **Prompt for missing required features**
- User fills in missing info
- Complete feature vector
- Predict outcome

**Key Innovation:**
- **Interactive feature engineering** with smart prompting
- **Same model** handles both existing and new trials
- **Feature schema** enforces consistency
- **Graceful degradation** with helpful error messages

---

Next: Implement the components!
