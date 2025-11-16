# TrialSense AI - User Experience Flow

## 🎯 Overview

TrialSense AI has **two interfaces** with the same underlying workflow:
1. **Streamlit Web App** - Interactive UI
2. **FastAPI REST API** - Programmatic access

Both require only **one simple input**: A natural language query.

---

## 🖥️ Streamlit App Flow (Recommended for Demo)

### **Step 1: Launch the App**

```bash
streamlit run trialsense/app/streamlit_app.py
```

Browser opens to `http://localhost:8501`

### **Step 2: User Sees Landing Page**

```
┌─────────────────────────────────────────────────────┐
│  🧬 TrialSense AI                                   │
│  Agentic AI System for Clinical Trial Intelligence │
│                                                      │
│  Powered by LangGraph Multi-Agent System            │
│                                                      │
│  This system uses specialized AI agents to:         │
│  🎯 Predict trial outcomes                          │
│  🏥 Match optimal trial sites                       │
│  📊 Provide evidence-based insights                 │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ Enter your query:                           │   │
│  │ ┌─────────────────────────────────────────┐ │   │
│  │ │ e.g., "Predict outcome for NCT04567890" │ │   │
│  │ └─────────────────────────────────────────┘ │   │
│  │                                             │   │
│  │  [🚀 Analyze]  [🗑️ Clear]                  │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  Sidebar shows:                                      │
│  - Example queries                                   │
│  - System architecture diagram                       │
│  - About the agents                                  │
└─────────────────────────────────────────────────────┘
```

### **Step 3: User Provides Input**

**Only Input Required:** A natural language query

**Three Types of Queries:**

#### **Type 1: Outcome Prediction**
```
"Predict outcome for trial NCT04567890"
"What is the success probability for NCT03842513?"
"Analyze the likelihood of success for a Phase 3 lung cancer trial"
```

#### **Type 2: Site Matching**
```
"Recommend sites for a Phase 3 lung cancer immunotherapy trial"
"Which sites are best for a rare disease pediatric trial?"
"Find optimal locations for my oncology study"
```

#### **Type 3: Comprehensive Analysis**
```
"Analyze trial NCT04567890 comprehensively"
"Provide full analysis of NCT03842513"
"Give me everything about trial NCT12345678"
```

**No other input required!**
- ❌ No forms to fill out
- ❌ No file uploads
- ❌ No configuration
- ✅ Just natural language

### **Step 4: System Processes (Behind the Scenes)**

```
User Query
    ↓
┌─────────────────────────────────┐
│ Orchestrator                    │
│ - Analyzes query                │
│ - Extracts NCT ID (if present)  │
│ - Determines task type          │
└─────────────────────────────────┘
    ↓
    ├─→ "predict" or NCT ID found → Outcome Agent
    ├─→ "site" or "recommend"     → Site Agent
    └─→ "comprehensive"           → Both Agents
    ↓
┌─────────────────────────────────┐
│ Outcome Prediction Agent        │
│ 1. Retrieves trial details      │
│ 2. Finds similar trials (RAG)   │
│ 3. Runs ML prediction           │
│ 4. Generates explanation        │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Site Matching Agent             │
│ 1. Analyzes trial requirements  │
│ 2. Searches site database       │
│ 3. Evaluates performance        │
│ 4. Ranks recommendations        │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Synthesizer                     │
│ - Combines results              │
│ - Formats final response        │
│ - Adds reasoning trace          │
└─────────────────────────────────┘
    ↓
Display to User
```

**Processing Time:** 5-15 seconds (depends on LLM response time)

### **Step 5: User Receives Results**

#### **Example 1: Outcome Prediction Response**

```
┌─────────────────────────────────────────────────────┐
│ 🎯 Outcome Prediction                               │
├─────────────────────────────────────────────────────┤
│                                                      │
│ === OUTCOME ANALYSIS ===                            │
│                                                      │
│ Trial Success Probability: 67% ±8%                  │
│                                                      │
│ Reasoning Chain:                                     │
│ 1. Retrieved trial NCT04567890: Phase 3 NSCLC      │
│    immunotherapy with 340 patients                  │
│                                                      │
│ 2. Found 127 similar historical trials via RAG      │
│                                                      │
│ 3. Key Positive Factors:                            │
│    ✓ Sponsor has 78% historical success rate        │
│    ✓ Strong Phase 2 biomarker data                  │
│    ✓ Optimal enrollment size (n=340)                │
│    ✓ Randomized, double-blind design                │
│                                                      │
│ 4. Risk Factors:                                     │
│    ⚠ Competitive landscape (3 similar trials)       │
│    ⚠ Composite endpoint complexity                  │
│    ⚠ Multi-center coordination required             │
│                                                      │
│ 5. Similar Successful Trial: NCT02576431            │
│    - 89% protocol similarity                        │
│    - FDA approval achieved in 2021                  │
│    - Enrollment completed 4 months early            │
│                                                      │
│ Confidence: High (based on 127 similar trials)      │
│                                                      │
│ ─────────────────────────────────────────────────── │
│ 🔍 View Reasoning Trace (expandable)                │
│   Step 1: Routed to outcome_prediction              │
│   Step 2: Completed outcome prediction              │
│   Step 3: Synthesis complete                        │
└─────────────────────────────────────────────────────┘
```

#### **Example 2: Site Matching Response**

```
┌─────────────────────────────────────────────────────┐
│ 🏥 Site Matching                                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│ === SITE RECOMMENDATIONS ===                        │
│                                                      │
│ Top 5 Site Matches for Phase 3 Lung Cancer Trial:  │
│                                                      │
│ 🥇 1. Johns Hopkins Sidney Kimmel Cancer Center     │
│    Match Score: 94/100                              │
│    Location: Baltimore, MD                          │
│                                                      │
│    ✅ Strong Fits:                                  │
│    • 850K eligible patients in catchment area       │
│    • Enrolled 127% of target on similar trial       │
│    • Dedicated immunotherapy unit                   │
│    • Avg IRB approval: 6.2 weeks                    │
│                                                      │
│    ⚠️ Considerations:                               │
│    • Currently running 3 competing PD-1 trials      │
│    • PI availability: 40% allocated                 │
│                                                      │
│    💡 Agent Insight:                                │
│    Site excels in patient recruitment but may       │
│    need dedicated coordinator. Similar trial        │
│    NCT04123 enrolled 45 pts in 8 months.           │
│                                                      │
│ 🥈 2. Dana-Farber Cancer Institute                  │
│    Match Score: 91/100                              │
│    Location: Boston, MA                             │
│    [... details ...]                                │
│                                                      │
│ [View Full Details for All 5 Sites]                 │
└─────────────────────────────────────────────────────┘
```

#### **Example 3: Comprehensive Analysis Response**

```
┌─────────────────────────────────────────────────────┐
│ 📊 Comprehensive Analysis                           │
├─────────────────────────────────────────────────────┤
│                                                      │
│ === OUTCOME ANALYSIS ===                            │
│ [Full outcome prediction as above]                  │
│                                                      │
│ === SITE RECOMMENDATIONS ===                        │
│ [Full site matching as above]                       │
│                                                      │
│ === SYNTHESIS ===                                   │
│                                                      │
│ Trial NCT04567890 shows strong potential (67%)      │
│ based on historical precedent and design quality.   │
│                                                      │
│ Recommended Action Plan:                            │
│ 1. Proceed with trial activation                    │
│ 2. Prioritize Johns Hopkins and Dana-Farber        │
│ 3. Allocate dedicated site coordinators            │
│ 4. Monitor competitive trial enrollment            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### **Step 6: User Can Interact Further**

**Options:**
1. **Ask Follow-up Questions**
   - "What about sites in California?"
   - "Why is the success rate 67%?"
   - "Show me the SHAP values"

2. **Try Another Query**
   - Click "Clear" and enter new query

3. **Explore Example Queries**
   - Click sidebar examples to auto-populate

4. **View Reasoning Trace**
   - Expand to see agent decision flow

---

## 🔌 FastAPI Flow (For Developers)

### **Step 1: Start the API**

```bash
uvicorn trialsense.api.main:app --reload
```

API available at `http://localhost:8000`

### **Step 2: Make Request**

**Endpoint:** `POST /analyze`

**Input Format:**
```json
{
  "query": "Predict outcome for trial NCT04567890"
}
```

**That's it!** Just one field: `query`

### **Step 3: Receive Response**

**Output Format:**
```json
{
  "query": "Predict outcome for trial NCT04567890",
  "response": "=== OUTCOME ANALYSIS ===\n\nTrial Success Probability: 67% ±8%\n\n...",
  "task_type": "outcome_prediction",
  "reasoning_trace": [
    "Routed to: outcome_prediction",
    "Completed outcome prediction",
    "Synthesis complete"
  ]
}
```

### **Example API Usage**

#### **Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"query": "Predict outcome for NCT04567890"}
)

result = response.json()
print(result["response"])
```

#### **cURL:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Predict outcome for NCT04567890"}'
```

#### **JavaScript:**
```javascript
fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: 'Predict outcome for NCT04567890'
  })
})
.then(r => r.json())
.then(data => console.log(data.response));
```

### **Streaming Endpoint**

**For Real-time Updates:**

```bash
curl -X POST http://localhost:8000/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Predict outcome for NCT04567890"}' \
  --no-buffer
```

**Stream Output:**
```
data: {"status": "started", "message": "Analyzing query..."}

data: {"type": "reasoning", "step": 1, "message": "Routed to: outcome_prediction"}

data: {"type": "response", "content": "=== OUTCOME ANALYSIS ===\n\nTrial Success Probability: 67%..."}

data: {"status": "complete", "task_type": "outcome_prediction"}
```

---

## 📋 Required vs Optional Inputs

### **Required:**
✅ **Query** (string, 1-1000 characters)
   - Natural language question about clinical trials
   - Can mention NCT IDs or general topics

### **Optional:**
❌ None! That's it.

### **NOT Required:**
- ❌ Trial details (we fetch them)
- ❌ Configuration files
- ❌ Uploaded data
- ❌ Forms with multiple fields
- ❌ Selection of specific agents
- ❌ Model parameters

**The system automatically:**
1. ✅ Detects NCT IDs in the query
2. ✅ Determines which agents to activate
3. ✅ Fetches trial data from ClinicalTrials.gov
4. ✅ Retrieves similar trials from vector store
5. ✅ Runs ML predictions
6. ✅ Synthesizes results

---

## 🎨 UX Design Principles

### **1. Simplicity**
```
Traditional Trial Analysis Tool:
├─ Upload protocol PDF
├─ Fill out 20+ form fields
├─ Select analysis type
├─ Configure parameters
├─ Wait for batch processing
└─ Download report (24 hours later)

TrialSense AI:
├─ Type natural language query
└─ Get instant analysis (15 seconds)
```

### **2. Intelligent Routing**
```
User doesn't choose agents - system decides:

"Predict outcome for NCT..." → Outcome Agent
"Recommend sites for..."    → Site Agent
"Analyze trial NCT..."       → Both Agents
```

### **3. Conversational Interface**
```
User can ask naturally:
✅ "What's the success rate for NCT04567890?"
✅ "Show me good sites for lung cancer"
✅ "Analyze NCT12345678"

Not required to learn syntax:
❌ {"action": "predict", "nct_id": "NCT04567890"}
```

### **4. Progressive Disclosure**
```
Initial view: Clean, simple query box

After analysis:
├─ Main results (always visible)
├─ Reasoning trace (expandable)
└─ Technical details (on demand)
```

### **5. Transparency**
```
Every response shows:
✅ Reasoning steps
✅ Data sources (NCT IDs cited)
✅ Confidence levels
✅ Limitations/caveats
```

---

## 🔄 Complete User Journey

### **Journey 1: Academic Researcher**

```
1. Opens Streamlit app
2. Types: "Predict outcome for my Phase 3 NSCLC trial NCT04567890"
3. Sees: 67% success probability with detailed reasoning
4. Asks follow-up: "Why only 67%?"
5. Gets explanation of risk factors
6. Satisfied, shares report with team
```

**Total time:** 30 seconds

### **Journey 2: Clinical Trial Manager**

```
1. Opens Streamlit app
2. Types: "Recommend sites for Phase 3 immunotherapy trial"
3. Gets: Top 5 sites with match scores
4. Clicks example: "Evaluate site performance for Johns Hopkins"
5. Sees: Historical metrics, success rates
6. Exports recommendations
```

**Total time:** 1 minute

### **Journey 3: Data Scientist (API)**

```python
# 1. Make API call
results = []
for nct_id in trial_ids:
    response = requests.post(
        "http://localhost:8000/analyze",
        json={"query": f"Predict outcome for {nct_id}"}
    )
    results.append(response.json())

# 2. Analyze results
success_rates = [r['response'] for r in results]

# 3. Generate report
create_batch_report(success_rates)
```

**Total time:** 5 minutes for 100 trials

---

## 📊 Input/Output Summary

### **Input:**
```json
{
  "query": "Natural language question"
}
```

### **Output:**
```json
{
  "query": "Original question",
  "response": "Comprehensive analysis with citations",
  "task_type": "outcome_prediction | site_matching | comprehensive",
  "reasoning_trace": ["Step 1", "Step 2", "..."]
}
```

### **Internal Processing (Hidden from User):**
```
1. Query Analysis
   ├─ Extract NCT IDs
   ├─ Detect intent
   └─ Route to agents

2. Data Gathering
   ├─ Fetch from ClinicalTrials.gov API
   ├─ Vector search (RAG)
   └─ Load ML models

3. Agent Execution
   ├─ Outcome Agent (if needed)
   ├─ Site Agent (if needed)
   └─ LLM synthesis

4. Response Generation
   ├─ Format results
   ├─ Add citations
   └─ Create reasoning trace
```

---

## 🎯 Key Takeaway

**User provides:** Just a natural language query

**System handles everything else:**
- ✅ Understanding intent
- ✅ Finding relevant data
- ✅ Running ML models
- ✅ Coordinating agents
- ✅ Synthesizing results
- ✅ Explaining reasoning

**Result:** ChatGPT-like simplicity with multi-agent sophistication under the hood!

---

## 🚀 Quick Start Examples

Try these queries to see different flows:

1. **Outcome Prediction:**
   ```
   "Predict outcome for trial NCT04567890"
   ```

2. **Site Matching:**
   ```
   "Find the best sites for a pediatric oncology trial"
   ```

3. **Comprehensive:**
   ```
   "Analyze trial NCT03842513 comprehensively"
   ```

4. **General:**
   ```
   "What makes a clinical trial successful?"
   ```

Each demonstrates different agent routing and capabilities!

---

**See Also:**
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Setup instructions
- [api_usage.md](api_usage.md) - API documentation
- [README.md](../README.md) - Project overview
