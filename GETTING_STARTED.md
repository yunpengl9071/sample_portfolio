# Getting Started with TrialSense AI

## Quick Start Guide

### Step 1: Clone and Setup

```bash
# Navigate to the project
cd sample_portfolio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# You need EITHER OpenAI OR Anthropic (or both)
```

Add to `.env`:
```
OPENAI_API_KEY=sk-proj-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Run the Demo

```bash
# Launch Streamlit app
streamlit run trialsense/app/streamlit_app.py
```

Your browser should open to `http://localhost:8501`

### Step 4: Try Example Queries

In the Streamlit app, try:

1. **Outcome Prediction**
   ```
   Predict the success probability for trial NCT04567890
   ```

2. **Site Matching**
   ```
   Recommend optimal sites for a Phase 3 lung cancer immunotherapy trial
   ```

3. **Comprehensive Analysis**
   ```
   Provide comprehensive analysis for trial NCT03842513
   ```

## Understanding the System

### What Happens Behind the Scenes?

When you submit a query:

1. **Router** analyzes your query and determines which agent(s) to activate
2. **Agents** use specialized tools to gather information:
   - Search clinical trials database
   - Retrieve detailed trial data
   - Run ML prediction models
   - Evaluate site performance
3. **LLM** synthesizes findings into coherent analysis
4. **Response** is streamed back with reasoning trace

### Architecture Overview

```
Your Query
    ↓
Orchestrator (LangGraph)
    ↓
┌─────────────┬─────────────┐
│   Outcome   │    Site     │
│   Agent     │   Matching  │
│             │   Agent     │
└─────────────┴─────────────┘
    ↓
Tools (Search, ML, RAG)
    ↓
Response with Evidence
```

## Development Workflow

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=trialsense --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black trialsense/

# Lint code
ruff check trialsense/

# Type checking
mypy trialsense/
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access app at http://localhost:8501
```

## Key Files to Explore

### For Understanding Agents
- `trialsense/agents/orchestrator.py` - LangGraph workflow
- `trialsense/agents/outcome_agent.py` - Outcome prediction
- `trialsense/agents/site_matching_agent.py` - Site matching

### For Understanding Tools
- `trialsense/tools/trial_search.py` - Vector search tools
- `trialsense/tools/prediction_tools.py` - ML prediction tools

### For Understanding Data
- `trialsense/data/clinical_trials_client.py` - API client
- `trialsense/data/vector_store.py` - ChromaDB integration
- `trialsense/models/outcome_predictor.py` - XGBoost model

### For Understanding Infrastructure
- `trialsense/config/settings.py` - Configuration
- `tests/` - Unit and integration tests
- `docs/architecture.md` - Detailed architecture

## Customization

### Add a New Tool

1. Create a new file in `trialsense/tools/`
2. Implement `BaseTool` interface:

```python
from langchain.tools import BaseTool

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "What this tool does..."

    def _run(self, param: str) -> str:
        # Your implementation
        return result
```

3. Add to agent's tools list in `trialsense/agents/`

### Add a New Agent

1. Create a new file in `trialsense/agents/`
2. Extend `BaseAgent`:

```python
from trialsense.agents.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        tools = [Tool1(), Tool2()]
        super().__init__(tools=tools)

    def _get_default_system_prompt(self) -> str:
        return "You are an expert in..."
```

3. Add to orchestrator workflow

### Modify LangGraph Workflow

Edit `trialsense/agents/orchestrator.py`:

```python
# Add new node
workflow.add_node("my_new_step", my_function)

# Add edge
workflow.add_edge("existing_node", "my_new_step")
```

## Troubleshooting

### "No module named 'trialsense'"

Make sure you're in the project root and have installed dependencies:
```bash
pip install -e .
```

### "API key not configured"

Check your `.env` file has valid API keys:
```bash
cat .env | grep API_KEY
```

### "Rate limit exceeded"

The ClinicalTrials.gov API has rate limits. The client automatically retries with backoff, but you may need to wait a few minutes if you make many requests.

### Vector store errors

If ChromaDB has issues, try clearing the data:
```bash
rm -rf data/vector_stores/*
```

## Next Steps

### Immediate Enhancements
- [ ] Populate vector store with real trial data
- [ ] Train ML model on historical outcomes
- [ ] Add more specialized agents
- [ ] Implement FastAPI backend

### Learning Resources
- LangGraph: https://langchain-ai.github.io/langgraph/
- LangChain: https://python.langchain.com/
- SHAP: https://shap.readthedocs.io/
- ClinicalTrials.gov API: https://clinicaltrials.gov/data-api/api

## Support

For questions or issues:
1. Check the [README](README.md)
2. Review [Architecture docs](docs/architecture.md)
3. Look at example tests in `tests/`
4. Open an issue on GitHub

---

**Happy Coding!** 🚀
