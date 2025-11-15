# TrialSense AI - Architecture Documentation

## System Overview

TrialSense AI is a **multi-agent AI system** built using LangGraph for orchestrating specialized agents that analyze clinical trials.

## Architecture Principles

### 1. Separation of Concerns
- **Agents**: High-level reasoning and orchestration
- **Tools**: Specific capabilities (search, prediction, retrieval)
- **Models**: ML inference and data processing
- **Data Layer**: API clients, vector stores, databases

### 2. Modularity
Each component is independently testable and replaceable:
- Swap LLM providers (OpenAI ↔ Anthropic)
- Replace vector store (Chroma ↔ Weaviate)
- Update ML models without changing agent code

### 3. Extensibility
Adding new capabilities:
- **New Tool**: Implement `BaseTool` interface
- **New Agent**: Extend `BaseAgent` class
- **New Workflow**: Add nodes to LangGraph

## Component Architecture

### LangGraph Orchestrator

```python
class TrialAnalysisState(TypedDict):
    messages: Sequence[BaseMessage]
    query: str
    task_type: Literal["outcome", "sites", "comprehensive"]
    outcome_prediction: Optional[str]
    site_recommendations: Optional[str]
    final_response: str
    reasoning_trace: list[str]
```

**Key Features:**
- **State Management**: Immutable state transitions
- **Conditional Routing**: Dynamic workflow based on query
- **Error Handling**: Graceful degradation
- **Observability**: Reasoning trace for debugging

### Agent Design

All agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    def __init__(self, tools, llm, system_prompt):
        self.tools = tools
        self.llm = llm
        self.agent_executor = create_agent_executor()

    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        pass

    async def arun(self, input_text, chat_history):
        # Execute agent with tools
```

**Specialized Agents:**

1. **OutcomePredictionAgent**
   - Tools: TrialSearch, SimilarTrials, MLPrediction
   - Purpose: Predict trial success with evidence
   - Output: Probability + explanations

2. **SiteMatchingAgent**
   - Tools: SiteSearch, SitePerformance
   - Purpose: Recommend optimal trial sites
   - Output: Ranked site list with rationale

### Tool Architecture

Tools are LangChain `BaseTool` implementations:

```python
class TrialSearchTool(BaseTool):
    name = "search_clinical_trials"
    description = "Search for clinical trials..."

    async def _arun(self, query: str, top_k: int) -> str:
        results = await vector_store.search(query, top_k)
        return format_results(results)
```

**Tool Categories:**

1. **Search Tools**: Vector similarity search
2. **Retrieval Tools**: Fetch detailed trial data
3. **Prediction Tools**: ML model inference
4. **Analysis Tools**: Site evaluation, comparisons

### Data Layer

#### ClinicalTrialsClient

Robust API client with:
- Retry logic (exponential backoff)
- Rate limiting (token bucket)
- Structured parsing
- Error handling

```python
@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=16)
)
async def _make_request(endpoint, params):
    await self._wait_for_rate_limit()
    response = await self._client.get(endpoint, params)
    return response.json()
```

#### TrialVectorStore

ChromaDB-backed vector storage:
- Sentence-transformers embeddings
- Metadata filtering
- Hybrid search (semantic + filters)
- Persistent storage

```python
# Indexing
embeddings = model.encode(trial_texts)
collection.upsert(ids, embeddings, metadatas)

# Searching
query_embedding = model.encode(query)
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k,
    where=filters
)
```

### ML Pipeline

#### Feature Engineering

Extract 20+ features from trial data:
- Numeric: enrollment, complexity metrics
- Categorical: phase, sponsor type
- Derived: historical success rates

```python
features = {
    "phase_numeric": encode_phase(),
    "enrollment_log": np.log1p(enrollment),
    "is_randomized": binary_feature(),
    "sponsor_success_rate": calculate_historical_rate()
}
```

#### XGBoost Model

- Binary classification (success/failure)
- Gradient boosting for tabular data
- Hyperparameter tuning with Optuna
- Cross-validation for robustness

#### SHAP Explainability

- TreeExplainer for XGBoost
- Feature importance ranking
- Local explanations per prediction
- LLM translation to natural language

## Data Flow

### Example: Outcome Prediction Query

```
User: "Predict outcome for NCT04567890"
  ↓
Orchestrator (Router Node)
  ↓ [task_type = "outcome_prediction"]
  ↓
Outcome Prediction Agent
  ↓
[Tool 1] TrialRetrievalTool
  → Fetch trial details from ClinicalTrials.gov API
  → Parse into structured ClinicalTrial object
  ↓
[Tool 2] SimilarTrialsTool
  → Generate embedding for trial
  → Vector search in ChromaDB
  → Return top 10 similar trials
  ↓
[Tool 3] PredictOutcomeTool
  → Extract features from trial
  → Run XGBoost inference
  → Calculate SHAP values
  → Format prediction + explanations
  ↓
Agent (LLM Synthesis)
  → Combine tool outputs
  → Generate coherent narrative
  → Cite evidence with NCT IDs
  ↓
Orchestrator (Synthesizer Node)
  → Format final response
  → Add reasoning trace
  ↓
User receives comprehensive analysis
```

## Scalability Considerations

### Current Limitations
- Vector store: In-memory (limited by RAM)
- API rate limits: 20 req/min for ClinicalTrials.gov
- LLM costs: GPT-4 calls can be expensive

### Production Scaling

1. **Vector Store**
   - Use Weaviate/Pinecone for distributed storage
   - Implement sharding for 1M+ trials
   - Add caching layer (Redis)

2. **API Client**
   - Batch requests where possible
   - Cache frequently accessed trials
   - Consider self-hosting trial database

3. **LLM Optimization**
   - Use streaming for real-time responses
   - Implement prompt caching
   - Consider smaller models for simple queries

4. **Compute**
   - Async processing throughout
   - Celery for background tasks
   - Kubernetes for horizontal scaling

## Security & Privacy

### API Keys
- Environment-based configuration
- Never commit keys to git
- Use secrets management (AWS Secrets Manager)

### Data Privacy
- No PHI (Protected Health Information)
- Public trial data only
- Compliance: HIPAA not required (no patient data)

### Rate Limiting
- Respect ClinicalTrials.gov terms
- Implement backoff on errors
- Monitor usage patterns

## Observability

### Logging
- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Context propagation

### Tracing
- LangSmith integration
- Agent execution traces
- Tool call tracking

### Metrics
- Query latency
- Agent success rates
- Tool usage patterns
- LLM token consumption

## Testing Strategy

### Unit Tests
- Pure functions
- Data models
- Feature extraction
- Tool implementations

### Integration Tests
- API client with mocked responses
- Vector store operations
- End-to-end agent workflows

### Evaluation
- ML model metrics (AUC, precision, recall)
- LLM-as-judge for agent outputs
- Human evaluation for quality

## Future Architecture Enhancements

### 1. Memory Layer
- Conversation history persistence
- User preference learning
- Trial watchlists

### 2. Multi-Modal
- PDF protocol parsing
- Figure/chart analysis
- Structured data extraction

### 3. Feedback Loop
- User corrections
- Active learning
- Model retraining pipeline

### 4. Microservices
- Separate services for agents
- API gateway
- Service mesh (Istio)

---

**Last Updated:** 2024-11-15
