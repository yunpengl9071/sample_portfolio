"""
FastAPI Backend for TrialSense AI

Provides REST API endpoints with streaming support for real-time agent responses.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from trialsense.agents.orchestrator import TrialSenseOrchestrator
from trialsense.config import get_settings
from trialsense.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and cleanup on shutdown."""
    setup_logging()
    logger.info("Starting TrialSense AI API")

    # Initialize orchestrator (cached)
    app.state.orchestrator = TrialSenseOrchestrator()

    yield

    logger.info("Shutting down TrialSense AI API")


# Create FastAPI app
app = FastAPI(
    title="TrialSense AI API",
    description="Agentic AI system for clinical trial intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AnalysisRequest(BaseModel):
    """Request model for trial analysis."""

    query: str = Field(
        ...,
        description="Natural language query about clinical trials",
        min_length=1,
        max_length=1000,
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )


class AnalysisResponse(BaseModel):
    """Response model for trial analysis."""

    query: str
    response: str
    task_type: str
    reasoning_trace: list[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    llm_providers: list[str]


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns API status and available LLM providers.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_providers=settings.get_available_llm_providers(),
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_trial(request: AnalysisRequest):
    """
    Analyze a clinical trial query.

    Returns comprehensive analysis with outcome predictions and/or site recommendations.

    Example request:
    ```json
    {
        "query": "Predict outcome for trial NCT04567890"
    }
    ```
    """
    try:
        orchestrator = app.state.orchestrator

        logger.info(f"Received analysis request: {request.query}")

        # Run orchestrator
        result = await orchestrator.arun(request.query)

        return AnalysisResponse(
            query=request.query,
            response=result["response"],
            task_type=result["task_type"],
            reasoning_trace=result["reasoning_trace"],
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


async def stream_analysis(query: str) -> AsyncIterator[str]:
    """
    Stream analysis results as Server-Sent Events.

    Yields:
        Server-sent event formatted strings
    """
    try:
        orchestrator = app.state.orchestrator

        # Send initial status
        yield f"data: {{'status': 'started', 'message': 'Analyzing query...'}}\n\n"

        # Run analysis
        result = await orchestrator.arun(query)

        # Stream reasoning trace
        for i, step in enumerate(result["reasoning_trace"]):
            yield f"data: {{'type': 'reasoning', 'step': {i+1}, 'message': '{step}'}}\n\n"

        # Stream final response in chunks
        response_text = result["response"]
        chunk_size = 100

        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            # Escape quotes and newlines for JSON
            chunk = chunk.replace('"', '\\"').replace('\n', '\\n')
            yield f"data: {{'type': 'response', 'content': '{chunk}'}}\n\n"

        # Send completion
        yield f"data: {{'status': 'complete', 'task_type': '{result['task_type']}'}}\n\n"

    except Exception as e:
        logger.error(f"Streaming analysis failed: {e}", exc_info=True)
        yield f"data: {{'status': 'error', 'message': '{str(e)}'}}\n\n"


@app.post("/analyze/stream")
async def analyze_trial_stream(request: AnalysisRequest):
    """
    Analyze a clinical trial query with streaming response.

    Returns Server-Sent Events (SSE) stream with:
    - Reasoning steps as they occur
    - Response chunks in real-time
    - Progress updates

    Example:
    ```bash
    curl -X POST http://localhost:8000/analyze/stream \
      -H "Content-Type: application/json" \
      -d '{"query": "Predict outcome for NCT04567890"}' \
      --no-buffer
    ```
    """
    return StreamingResponse(
        stream_analysis(request.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "TrialSense AI API",
        "version": "0.1.0",
        "description": "Agentic AI system for clinical trial intelligence",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "analyze_stream": "/analyze/stream",
            "docs": "/docs",
        }
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "trialsense.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
