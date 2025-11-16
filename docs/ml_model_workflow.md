# ML Model Training vs. Inference Workflow

## 🎯 Quick Answer

**No, model training does NOT happen during user interactions!**

```
Training (one-time) ──────┐
                          │
                    [Saved Model]
                          │
User Query ───> Load Model ───> Inference (fast) ───> Results
```

---

## 🔄 Two Separate Phases

### **Phase 1: Training (One-Time or Periodic)**

**When:** Before deploying the app (or periodically to refresh)

**How Long:** 5-50 minutes depending on data size

**Command:**
```bash
python scripts/train_model.py
```

**What Happens:**
```
1. Fetch historical trials (500-50K trials)
   └─ Takes: 5-30 minutes (API calls)

2. Extract features from trials
   └─ Takes: 30 seconds - 2 minutes

3. Train XGBoost model
   └─ Takes: 30 seconds - 5 minutes

4. Save model to disk
   └─ Saves to: models/outcome_model.json
   └─ File size: 1-10 MB

Total time: 10-50 minutes (one-time)
```

**Output:**
```
models/
└── outcome_model.json  (saved XGBoost model)
```

**Frequency:**
- Initially: Once
- Production: Weekly/Monthly (to incorporate new trial data)

### **Phase 2: Inference (Every User Query)**

**When:** Each time user asks for prediction

**How Long:** <0.1 seconds

**What Happens:**
```
1. Load pre-trained model from disk
   └─ Takes: <0.5 seconds (one-time per app startup)

2. Extract features from trial
   └─ Takes: <0.01 seconds

3. Run prediction
   └─ Takes: <0.01 seconds

4. Generate SHAP explanations
   └─ Takes: <0.05 seconds

Total time: <0.1 seconds per query
```

**NO retraining!** Just fast inference.

---

## 📊 Current Implementation

### **Option 1: Without Pre-trained Model (Demo Mode)**

If you run the app **without** training a model first:

```python
# In trialsense/models/outcome_predictor.py
class OutcomePredictor:
    def __init__(self, model_path=None):
        if model_path and Path(model_path).exists():
            self.load(model_path)  # Load existing
        else:
            self._initialize_model()  # Create new (untrained)
```

**What happens:**
```
User Query → Model not trained → Returns default/placeholder predictions
```

**For portfolio demo:** This is actually FINE because:
- Agents still work (use other tools)
- LLM still provides intelligent analysis
- Just the ML prediction is a placeholder

### **Option 2: With Pre-trained Model (Production Mode)**

**Step 1: Train once**
```bash
python scripts/train_model.py
```

**Step 2: Model is saved**
```
models/outcome_model.json created ✓
```

**Step 3: App loads model at startup**
```python
# App initialization (once)
outcome_model = OutcomePredictor(model_path="models/outcome_model.json")

# Every user query (fast)
result = outcome_model.predict(trial)  # <0.1 seconds
```

---

## 🔍 Detailed Workflow Diagram

### **Training Workflow (One-Time)**

```
┌─────────────────────────────────────────────────────┐
│ TRAINING PHASE (Offline, One-Time)                  │
└─────────────────────────────────────────────────────┘

python scripts/train_model.py
        ↓
┌───────────────────────┐
│ 1. Fetch Historical   │
│    Trials from API    │
│    (500-50K trials)   │
│    ⏱ 5-30 min         │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ 2. Feature            │
│    Engineering        │
│    ⏱ 1-2 min          │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ 3. Train XGBoost      │
│    Model              │
│    ⏱ 30 sec - 5 min   │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ 4. Evaluate Model     │
│    (AUC, precision)   │
│    ⏱ 10 sec           │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ 5. Save Model         │
│    models/*.json      │
│    ⏱ 1 sec            │
└───────────────────────┘
        ↓
    ✓ Model Ready
```

### **Inference Workflow (Every User Query)**

```
┌─────────────────────────────────────────────────────┐
│ INFERENCE PHASE (Online, Real-Time)                 │
└─────────────────────────────────────────────────────┘

User: "Predict outcome for NCT04567890"
        ↓
┌───────────────────────┐
│ Load Pre-trained      │
│ Model (if needed)     │
│ ⏱ <0.5 sec            │
│ (cached after first)  │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ Fetch Trial Data      │
│ from API              │
│ ⏱ 1-2 sec             │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ Extract Features      │
│ ⏱ <0.01 sec           │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ Model.predict()       │
│ ⏱ <0.01 sec           │
└───────────────────────┘
        ↓
┌───────────────────────┐
│ SHAP Explanations     │
│ ⏱ <0.05 sec           │
└───────────────────────┘
        ↓
    Results (67% success)
```

**Total inference time: <0.1 seconds**

---

## 💻 How to Use

### **Scenario 1: Quick Demo (No Training)**

```bash
# Just run the app
streamlit run trialsense/app/streamlit_app.py

# ML predictions will use placeholder values
# LLM agents still provide intelligent analysis
```

**Good for:**
- Quick portfolio demo
- Showing architecture
- Testing agent orchestration

### **Scenario 2: Full Demo (With Training)**

```bash
# Step 1: Train model once (10-30 min)
python scripts/train_model.py

# Step 2: Run app (model loads automatically)
streamlit run trialsense/app/streamlit_app.py

# Now ML predictions use real trained model
```

**Good for:**
- Production deployment
- Accurate predictions
- Full system demonstration

### **Scenario 3: Development (Train Small)**

```bash
# Train on small dataset (fast for testing)
python scripts/train_model.py  # Uses 500 trials by default

# Quick training (~2 minutes)
# Still demonstrates ML pipeline
```

---

## 🔧 Code Implementation

### **Current Code (Auto-Handles Both Cases)**

```python
# trialsense/models/outcome_predictor.py

class OutcomePredictor:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize predictor.

        If model_path exists: Load pre-trained model
        Otherwise: Create new untrained model (for demo)
        """
        self.model: Optional[xgb.XGBClassifier] = None

        if model_path and Path(model_path).exists():
            self.load(model_path)  # Load existing
            logger.info(f"Loaded pre-trained model from {model_path}")
        else:
            self._initialize_model()  # Create new
            logger.warning("No pre-trained model found. Using untrained model.")

    def predict(self, trial: ClinicalTrial) -> PredictionResult:
        """Fast prediction using pre-trained model."""
        if not self.model:
            logger.warning("Model not trained, returning default prediction")
            return self._default_prediction()

        # Extract features (fast)
        features = self._extract_features(trial)
        X = self._prepare_features_for_model(features)

        # Predict (very fast, <0.01 sec)
        proba = self.model.predict_proba(X.reshape(1, -1))[0][1]

        # SHAP explanation (fast, <0.05 sec)
        shap_values = self.explainer.shap_values(X.reshape(1, -1))

        return PredictionResult(
            success_probability=float(proba),
            # ... rest of result
        )
```

### **Updated Agent Code (Graceful Degradation)**

```python
# trialsense/agents/outcome_agent.py

class OutcomePredictionAgent(BaseAgent):
    def __init__(self, outcome_model=None, **kwargs):
        # Try to load pre-trained model
        model_path = "models/outcome_model.json"

        if outcome_model:
            self.outcome_model = outcome_model
        elif Path(model_path).exists():
            self.outcome_model = OutcomePredictor(model_path)
            logger.info("✓ Loaded pre-trained ML model")
        else:
            self.outcome_model = OutcomePredictor()
            logger.warning("⚠ No pre-trained model. ML predictions will be estimates.")

        # Rest of initialization...
```

---

## 📋 Training Data Requirements

### **Minimum for Demo:**
```python
# In scripts/train_model.py
trials, labels = await fetch_training_data(max_trials=500)
```
- **500 trials**
- **~5 minutes** to fetch
- **~2 minutes** to train
- **Good enough** for demo

### **Recommended for Production:**
```python
trials, labels = await fetch_training_data(max_trials=5000)
```
- **5,000 trials**
- **~20 minutes** to fetch
- **~5 minutes** to train
- **Better accuracy**

### **Maximum (Research Quality):**
```python
trials, labels = await fetch_training_data(max_trials=50000)
```
- **50,000 trials**
- **~2 hours** to fetch
- **~15 minutes** to train
- **Best accuracy**

---

## 🎯 Key Takeaways

### **Training:**
```
✅ Done ONCE (offline)
✅ Takes 10-50 minutes
✅ Saves model to disk
✅ Optional for demo
✅ Required for production
```

### **Inference (User Queries):**
```
✅ Loads saved model (fast)
✅ Takes <0.1 seconds
✅ No retraining
✅ Just prediction
```

### **Does NOT Happen on Every Query:**
```
❌ Fetching training data
❌ Model training
❌ Hyperparameter tuning
❌ Model evaluation
```

### **DOES Happen on Every Query:**
```
✅ Load model (if not cached)
✅ Extract features
✅ Run prediction
✅ Generate SHAP values
```

---

## 🚀 Recommended Workflow for Your Portfolio

### **For Demo/Interview:**

**Option A: No Training (Fastest)**
```bash
# Just run - works immediately
streamlit run trialsense/app/streamlit_app.py

# Agents work, LLM analysis works
# ML predictions are placeholders (still shows architecture)
```

**Option B: Quick Training (Best)**
```bash
# 1. Train small model (~5 minutes)
python scripts/train_model.py

# 2. Run app with real model
streamlit run trialsense/app/streamlit_app.py

# Everything works with real predictions!
```

### **For Production Deployment:**

```bash
# 1. Train comprehensive model (one-time, ~30 min)
python scripts/train_model.py

# 2. Deploy app (model loads automatically)
docker-compose up

# 3. Periodic retraining (monthly)
cron: 0 0 1 * * python scripts/train_model.py
```

---

## 🔄 Model Update Strategy

### **Development:**
```
Train once → Use for all testing
```

### **Production:**
```
Initial: Train with historical data
Monthly: Retrain with new completed trials
On-demand: Retrain when data quality improves
```

### **Model Versioning:**
```
models/
├── outcome_model_v1.json      (initial)
├── outcome_model_v2.json      (updated)
└── outcome_model_latest.json  (symlink to current)
```

---

## 💡 Bottom Line

**Do you need to pretrain?**
- **For demo:** No, but recommended (5 min training)
- **For production:** Yes (30 min training)

**Does it retrain on every query?**
- **No!** That would be way too slow
- Model trains once, predicts many times

**Performance:**
- **Training:** 10-50 minutes (one-time)
- **Inference:** <0.1 seconds (every query)

**Your laptop can handle:**
- ✅ Training: Yes (5-30 min, <4 GB RAM)
- ✅ Inference: Definitely (instant, <100 MB RAM)

---

**See Also:**
- [system_requirements.md](system_requirements.md) - Hardware needs
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Setup guide
- [scripts/train_model.py](../scripts/train_model.py) - Training script
