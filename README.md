# 🧬 TrialSense AI

**Agentic AI System for Clinical Trial Intelligence using LangGraph**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Project Overview

TrialSense AI is a production-ready **multi-agent AI system** that analyzes clinical trials using:
- **LangGraph** for agent orchestration
- **LangChain** for LLM tool integration
- **XGBoost + SHAP** for explainable outcome prediction
- **RAG** with vector embeddings for evidence retrieval
- **Public data** from ClinicalTrials.gov (400K+ trials)

### Why This Project?

This project demonstrates **modern AI engineering skills** essential for AI product/engineering roles:

✅ **Agentic AI Architecture**: Multi-agent orchestration using LangGraph state machines
✅ **LLM Engineering**: Prompt design, context management, tool integration
✅ **RAG Systems**: Vector search, hybrid retrieval, semantic matching
✅ **ML + LLM Hybrid**: Classical ML models enhanced with LLM reasoning
✅ **Production Code**: Modular architecture, testing, type hints, documentation
✅ **Healthcare Domain**: Real-world clinical trial data and analysis

---

## 🏗️ System Architecture

### Multi-Agent Workflow

```
┌─────────────────────────────────────────────────────┐
│            Orchestrator (LangGraph)                 │
│         State Management & Routing                  │
└─────────────────────────────────────────────────────┘
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
┌──────────────────┐    ┌──────────────────┐
│ Outcome          │    │ Site Matching    │
│ Prediction Agent │    │ Agent            │
└──────────────────┘    └──────────────────┘
        ↓                         ↓
   ┌─────────┐              ┌──────────┐
   │ Tools:  │              │ Tools:   │
   │ • Search│              │ • Search │
   │ • RAG   │              │ • Analyze│
   │ • ML    │              │ • Rank   │
   └─────────┘              └──────────┘
```

### Core Components

1. **LangGraph Orchestrator**: Routes queries, coordinates agents, manages state
2. **Outcome Prediction Agent**: ML-powered trial success prediction with explainability
3. **Site Matching Agent**: Multi-dimensional site recommendation system
4. **Vector Store**: ChromaDB with 400K+ trial embeddings for semantic search
5. **ML Models**: XGBoost classifier with SHAP for interpretable predictions
6. **API Client**: Robust ClinicalTrials.gov integration with retry logic

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key or Anthropic API key
- 2GB+ RAM for vector embeddings

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trialsense-ai.git
cd trialsense-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install

# Or use pip
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Optional: LangSmith for tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
```

### Run the Demo

```bash
# Launch Streamlit app
streamlit run trialsense/app/streamlit_app.py

# Or use the orchestrator directly
python -c "
from trialsense.agents.orchestrator import TrialSenseOrchestrator

orchestrator = TrialSenseOrchestrator()
result = orchestrator.run('Predict outcome for NCT04567890')
print(result['response'])
"
```

---

## 💡 Example Use Cases

### 1. Predict Trial Outcome

```python
from trialsense.agents.orchestrator import TrialSenseOrchestrator

orchestrator = TrialSenseOrchestrator()

result = orchestrator.run(
    "Analyze the success probability for trial NCT04567890"
)

print(result['response'])
```

**Output:**
```
=== OUTCOME ANALYSIS ===

Trial Success Probability: 67% ±8%

Reasoning Chain:
1. Retrieved trial NCT04567890: Phase 3 NSCLC immunotherapy
2. Found 127 similar historical trials
3. Key positive factors:
   - Sponsor has 78% historical success rate
   - Strong Phase 2 biomarker data
   - Optimal enrollment (n=340)

4. Risk factors:
   - Competitive landscape (3 similar ongoing trials)
   - Composite endpoint complexity

5. Similar successful trial: NCT02576431
   - 89% protocol similarity
   - FDA approval in 2021

Confidence: High
```

### 2. Match Optimal Sites

```python
result = orchestrator.run(
    "Recommend sites for a Phase 3 lung cancer immunotherapy trial"
)
```

**Output:**
```
=== SITE RECOMMENDATIONS ===

Top 5 Site Matches:

1. Johns Hopkins Sidney Kimmel Cancer Center (Score: 94/100)
   ✓ Enrolled 127% of target on similar trial NCT04123
   ✓ 850K eligible patients in catchment area
   ✓ Dedicated immunotherapy unit
   ⚠ Currently running 3 competing trials

2. Dana-Farber Cancer Institute (Score: 91/100)
   ...
```

### 3. Comprehensive Analysis

```python
result = orchestrator.run(
    "Provide comprehensive analysis for trial NCT03842513"
)
```

Combines outcome prediction + site matching + literature evidence.

---

## 🔬 Technical Deep Dive

### LangGraph Orchestration

The system uses **LangGraph** for stateful multi-agent coordination:

```python
# Simplified workflow
class TrialAnalysisState(TypedDict):
    query: str
    task_type: Literal["outcome", "sites", "comprehensive"]
    outcome_prediction: Optional[str]
    site_recommendations: Optional[str]
    final_response: str

workflow = StateGraph(TrialAnalysisState)

# Add nodes (agents)
workflow.add_node("router", route_query)
workflow.add_node("outcome_predictor", predict_outcome)
workflow.add_node("site_matcher", match_sites)
workflow.add_node("synthesizer", synthesize_results)

# Conditional routing
workflow.add_conditional_edges(
    "router",
    route_decision,
    {"outcome": "outcome_predictor", "sites": "site_matcher"}
)
```

### RAG Pipeline

**Vector Store Setup:**
```python
from trialsense.data.vector_store import TrialVectorStore

store = TrialVectorStore()
await store.add_trials(trials)  # Index 400K trials

# Semantic search
results = await store.search(
    "lung cancer immunotherapy",
    top_k=10,
    phase="PHASE3"
)
```

**Hybrid Retrieval:**
- Semantic similarity via sentence-transformers
- Metadata filtering (phase, status, therapeutic area)
- Reranking based on relevance

### ML Model Pipeline

**Feature Engineering:**
```python
features = {
    "phase_numeric": encode_phase(trial.phase),
    "enrollment_log": np.log1p(trial.enrollment),
    "is_randomized": 1 if trial.allocation == "RANDOMIZED" else 0,
    "sponsor_track_record": get_historical_success_rate(),
    # ... 20+ features
}
```

**XGBoost Training:**
```python
from trialsense.models.outcome_predictor import OutcomePredictor

predictor = OutcomePredictor()
predictor.train(trials, labels, validation_split=0.2)

# Predict with explanations
result = predictor.predict(trial)
print(f"Probability: {result.success_probability:.2%}")
print(f"Top factors: {result.feature_importance}")
```

**SHAP Explanations:**
- Tree-based SHAP values for interpretability
- Feature importance ranking
- Natural language translation via LLM

---

## 📊 Data Sources (All Public)

1. **ClinicalTrials.gov API v2**
   - 400,000+ clinical trials
   - Structured metadata, eligibility criteria, outcomes
   - Real-time updates

2. **FDA Drug Approvals**
   - Historical approval data
   - Trial success indicators

3. **PubMed Central** (future)
   - Supporting medical literature
   - Citation graphs

4. **Mock Site Database**
   - Simulated site performance metrics
   - In production: integrate real site data

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=trialsense --cov-report=html

# Run specific test file
pytest tests/unit/test_clinical_trials_client.py -v

# Test agents
pytest tests/unit/test_agents.py -v
```

**Test Coverage:**
- ✅ Unit tests for all core modules
- ✅ Integration tests for API client
- ✅ Agent workflow tests
- ✅ Mock data for reproducibility

---

## 📁 Project Structure

```
trialsense-ai/
├── trialsense/
│   ├── agents/              # LangGraph agents
│   │   ├── base.py         # Base agent class
│   │   ├── orchestrator.py # LangGraph workflow
│   │   ├── outcome_agent.py
│   │   └── site_matching_agent.py
│   ├── data/               # Data layer
│   │   ├── clinical_trials_client.py  # API client
│   │   ├── vector_store.py           # ChromaDB
│   │   └── models.py                 # Pydantic models
│   ├── models/             # ML models
│   │   └── outcome_predictor.py      # XGBoost + SHAP
│   ├── tools/              # LangChain tools
│   │   ├── trial_search.py
│   │   ├── prediction_tools.py
│   │   └── site_tools.py
│   ├── config/             # Configuration
│   ├── utils/              # Utilities
│   └── app/                # Streamlit app
├── tests/                  # Test suite
├── notebooks/              # Jupyter notebooks
├── docs/                   # Documentation
├── pyproject.toml          # Poetry config
└── README.md              # This file
```

---

## 🎓 Key Learnings & Design Decisions

### 1. **Agentic Architecture**
   - **Why LangGraph?** Provides explicit state management and visual workflow debugging
   - **Agent Specialization:** Each agent has focused domain expertise
   - **Composability:** Agents can be combined for complex analyses

### 2. **Hybrid ML + LLM Approach**
   - **Classical ML:** XGBoost for reliable, calibrated predictions
   - **LLM Enhancement:** Natural language explanations, context retrieval
   - **Best of Both:** Accuracy + interpretability

### 3. **RAG Over Fine-Tuning**
   - **Flexibility:** Easy to update with new trials
   - **Explainability:** Can cite specific evidence
   - **Cost:** No expensive fine-tuning required

### 4. **Production Readiness**
   - Retry logic with exponential backoff
   - Rate limiting for API compliance
   - Type hints throughout
   - Comprehensive testing
   - Modular, extensible design

---

## 🔮 Future Enhancements

- [ ] **FastAPI Backend**: RESTful API with streaming responses
- [ ] **LLM-as-Judge**: Automated evaluation of agent outputs
- [ ] **Multi-Modal**: Incorporate trial protocol PDFs
- [ ] **Fine-Tuned Models**: Domain-specific LLM fine-tuning
- [ ] **Real Site Data**: Integration with actual site performance databases
- [ ] **Causal Analysis**: Beyond correlation to causal inference
- [ ] **Deployment**: Docker + Kubernetes configs for cloud deployment

---

## 📖 Documentation

- [Architecture Guide](docs/architecture.md) - Detailed system design
- [Agent Design](docs/agent_design.md) - Agent specifications
- [Context Engineering](docs/context_engineering.md) - Prompt design patterns
- [API Reference](docs/api_reference.md) - Code documentation

---

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ClinicalTrials.gov** for providing open access to clinical trial data
- **LangChain/LangGraph** team for excellent agent framework
- **Anthropic/OpenAI** for powerful LLM APIs
- **SHAP** library for model interpretability

---

## 📧 Contact

**Your Name** - AI Product Engineer

- Portfolio: [yourportfolio.com](https://yourportfolio.com)
- LinkedIn: [linkedin.com/in/yourname](https://linkedin.com/in/yourname)
- GitHub: [@yourusername](https://github.com/yourusername)

---

## 🌟 Star History

If you find this project helpful for learning about agentic AI systems, please consider giving it a star! ⭐

---

**Built with LangGraph, LangChain, XGBoost, ChromaDB, and Streamlit**

*Showcasing modern AI engineering for healthcare applications*
