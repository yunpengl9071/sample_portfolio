"""Application settings using Pydantic for validation."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")

    # LangSmith (Tracing)
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangSmith tracing")
    langchain_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langchain_project: str = Field(default="trialsense-ai", description="LangSmith project name")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # Database
    duckdb_path: str = Field(default="./data/trialsense.db", description="DuckDB database path")

    # Vector Store
    chroma_persist_dir: str = Field(
        default="./data/vector_stores", description="ChromaDB persistence directory"
    )

    # Model Settings
    default_llm: str = Field(
        default="gpt-4-turbo-preview", description="Default LLM model to use"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model"
    )
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=4096, gt=0, description="Max tokens for LLM responses")

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, gt=0, lt=65536, description="API port")
    api_reload: bool = Field(default=True, description="Enable auto-reload in development")

    # Clinical Trials API
    clinicaltrials_api_base: str = Field(
        default="https://clinicaltrials.gov/api/v2",
        description="ClinicalTrials.gov API base URL",
    )
    clinicaltrials_rate_limit: int = Field(
        default=20, gt=0, description="Requests per minute for ClinicalTrials.gov API"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Agent Settings
    agent_max_iterations: int = Field(
        default=15, gt=0, description="Max iterations for agent execution"
    )
    agent_timeout: int = Field(default=300, gt=0, description="Agent timeout in seconds")

    # RAG Settings
    retrieval_top_k: int = Field(default=10, gt=0, description="Top K results for retrieval")
    chunk_size: int = Field(default=1000, gt=0, description="Text chunk size for embeddings")
    chunk_overlap: int = Field(default=200, ge=0, description="Overlap between chunks")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v

    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.openai_api_key is not None and len(self.openai_api_key) > 0

    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured."""
        return self.anthropic_api_key is not None and len(self.anthropic_api_key) > 0

    def get_available_llm_providers(self) -> list[str]:
        """Get list of available LLM providers based on configured keys."""
        providers = []
        if self.has_openai_key():
            providers.append("openai")
        if self.has_anthropic_key():
            providers.append("anthropic")
        return providers


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
