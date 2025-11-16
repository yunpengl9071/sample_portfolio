# TrialSense AI - API Usage Guide

## FastAPI Backend

The FastAPI backend provides REST endpoints with optional streaming support for real-time agent responses.

### Starting the API Server

```bash
# Option 1: Using Python
python trialsense/api/main.py

# Option 2: Using uvicorn directly
uvicorn trialsense.api.main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Using Docker
docker-compose up
```

The API will be available at `http://localhost:8000`

### Interactive API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### 1. Health Check

**GET** `/health`

Check API status and available LLM providers.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "llm_providers": ["openai"]
}
```

### 2. Analyze Trial (Standard)

**POST** `/analyze`

Analyze a clinical trial query with standard response.

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Predict outcome for trial NCT04567890"
  }'
```

**Request Body:**
```json
{
  "query": "string (required, 1-1000 characters)",
  "stream": false
}
```

**Response:**
```json
{
  "query": "Predict outcome for trial NCT04567890",
  "response": "=== OUTCOME ANALYSIS ===\n\nTrial Success Probability: 67%...",
  "task_type": "outcome_prediction",
  "reasoning_trace": [
    "Routed to: outcome_prediction",
    "Completed outcome prediction"
  ]
}
```

### 3. Analyze Trial (Streaming)

**POST** `/analyze/stream`

Analyze with Server-Sent Events (SSE) streaming for real-time updates.

```bash
curl -X POST http://localhost:8000/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Recommend sites for lung cancer trial"
  }' \
  --no-buffer
```

**Response (SSE Stream):**
```
data: {"status": "started", "message": "Analyzing query..."}

data: {"type": "reasoning", "step": 1, "message": "Routed to: site_matching"}

data: {"type": "response", "content": "=== SITE RECOMMENDATIONS ===\n\nTop 5 Site Matches..."}

data: {"status": "complete", "task_type": "site_matching"}
```

**Example with JavaScript:**
```javascript
const eventSource = new EventSource('http://localhost:8000/analyze/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.status === 'started') {
    console.log('Analysis started');
  } else if (data.type === 'reasoning') {
    console.log(`Step ${data.step}: ${data.message}`);
  } else if (data.type === 'response') {
    console.log('Response chunk:', data.content);
  } else if (data.status === 'complete') {
    console.log('Analysis complete');
    eventSource.close();
  }
};
```

**Example with Python:**
```python
import requests

response = requests.post(
    'http://localhost:8000/analyze/stream',
    json={'query': 'Predict outcome for NCT04567890'},
    stream=True
)

for line in response.iter_lines():
    if line:
        # Remove 'data: ' prefix
        data = line.decode('utf-8').replace('data: ', '')
        print(data)
```

## Example Queries

### Outcome Prediction
```json
{
  "query": "What is the success probability for trial NCT04567890?"
}
```

```json
{
  "query": "Predict outcome for a Phase 3 oncology trial with 300 patients"
}
```

### Site Matching
```json
{
  "query": "Recommend sites for a Phase 3 lung cancer immunotherapy trial"
}
```

```json
{
  "query": "Which sites are best for a rare disease pediatric trial in the Northeast?"
}
```

### Comprehensive Analysis
```json
{
  "query": "Analyze trial NCT03842513 comprehensively"
}
```

```json
{
  "query": "Provide complete analysis of NCT04567890 including outcome prediction and site recommendations"
}
```

## Python Client Example

```python
import requests
from typing import Dict, Any

class TrialSenseClient:
    """Python client for TrialSense AI API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def health(self) -> Dict[str, Any]:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze a trial query."""
        response = requests.post(
            f"{self.base_url}/analyze",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()

    def analyze_stream(self, query: str):
        """Analyze with streaming response."""
        response = requests.post(
            f"{self.base_url}/analyze/stream",
            json={"query": query},
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                yield line.decode('utf-8').replace('data: ', '')

# Usage
client = TrialSenseClient()

# Check health
print(client.health())

# Standard analysis
result = client.analyze("Predict outcome for NCT04567890")
print(result['response'])

# Streaming analysis
for event in client.analyze_stream("Recommend sites for lung cancer trial"):
    print(event)
```

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **422**: Validation Error (invalid request body)
- **500**: Internal Server Error

**Error Response:**
```json
{
  "detail": "Analysis failed: Model not loaded"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production:

1. Add rate limiting middleware
2. Implement API keys
3. Add request quotas per user

## CORS Configuration

The API allows all origins by default. For production:

```python
# In trialsense/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Deployment

### Using Docker

```bash
# Build image
docker build -t trialsense-ai .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  trialsense-ai \
  uvicorn trialsense.api.main:app --host 0.0.0.0 --port 8000
```

### Using Docker Compose

```bash
# Start all services (API + Redis)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Cloud Deployment

**Heroku:**
```bash
heroku create trialsense-ai
heroku config:set OPENAI_API_KEY=your-key
git push heroku main
```

**AWS ECS / Google Cloud Run:**
- Use the provided Dockerfile
- Set environment variables for API keys
- Configure auto-scaling based on traffic

## Monitoring

### Health Checks
```bash
# Simple health check
curl http://localhost:8000/health

# With watch (every 5 seconds)
watch -n 5 curl http://localhost:8000/health
```

### Logging

Logs are output to stdout/stderr. Configure log aggregation:

```bash
# Docker logs
docker-compose logs -f trialsense

# Save to file
docker-compose logs > api_logs.txt
```

### Metrics (Future Enhancement)

Add Prometheus metrics:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('trialsense_requests_total', 'Total requests')
request_duration = Histogram('trialsense_request_duration_seconds', 'Request duration')
```

## Security Best Practices

1. **API Keys**: Store in environment variables, never commit
2. **HTTPS**: Use TLS/SSL in production
3. **Input Validation**: Pydantic models validate all inputs
4. **Rate Limiting**: Implement per-user quotas
5. **Monitoring**: Log all requests and errors

## Troubleshooting

### "No LLM providers available"
- Check that `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
- Verify API key is valid

### "Connection refused"
- Ensure server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify port 8000 is not in use

### "Streaming not working"
- Ensure using `--no-buffer` with curl
- Check browser EventSource implementation
- Verify Content-Type headers

---

**Next Steps:**
- See [GETTING_STARTED.md](../GETTING_STARTED.md) for setup
- See [architecture.md](architecture.md) for system design
- See [README.md](../README.md) for project overview
