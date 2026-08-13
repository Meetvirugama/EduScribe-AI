import time
from pydantic import BaseModel, ConfigDict, Field


class BaseLLMOutput(BaseModel):
    """
    Base schema for all AI pipeline outputs.
    Provides standard metadata across all pipeline stages.
    The fields are injected by the LLM Manager after validation.
    """
    model_config = ConfigDict(frozen=True, extra="ignore")

    # Metadata
    provider: str = Field(default="unknown")
    model: str = Field(default="unknown")
    latency: float = Field(default=0.0)
    total_tokens: int = Field(default=0)
    schema_version: str = Field(default="1.0")
    created_at: float = Field(default_factory=time.time)

    # Confidence score (optional, overridable by subclasses)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
