from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class TaskRequirements:
    """Requirements a model must meet to be considered for a task."""
    structured_output: bool = False
    requires_vision: bool = False
    min_context_window: int = 0
    quality_tier: str = "standard"  # e.g., "standard", "high", "fast"

@dataclass
class ModelCapabilities:
    """Capabilities provided by a specific model."""
    provider: str
    model: str
    supports_structured_output: bool = True
    supports_vision: bool = False
    max_context_window: int = 8192
    quality_tier: str = "standard"

# Centralized Registry of Model Capabilities
# Used by FallbackManager to filter models that cannot fulfill a task
MODEL_CAPABILITIES_REGISTRY: Dict[str, ModelCapabilities] = {
    # Gemini
    "gemini-2.5-flash": ModelCapabilities(
        provider="gemini", model="gemini-2.5-flash",
        supports_structured_output=True, supports_vision=True, max_context_window=1000000, quality_tier="high"
    ),
    
    # Cohere
    "command-a-plus-05-2026": ModelCapabilities(
        provider="cohere", model="command-a-plus-05-2026",
        supports_structured_output=True, supports_vision=False, max_context_window=128000, quality_tier="high"
    ),
    "command-a-05-2026": ModelCapabilities(
        provider="cohere", model="command-a-05-2026",
        supports_structured_output=True, supports_vision=False, max_context_window=128000, quality_tier="standard"
    ),

    # Groq
    "llama-3.3-70b-versatile": ModelCapabilities(
        provider="groq", model="llama-3.3-70b-versatile",
        supports_structured_output=True, supports_vision=False, max_context_window=128000, quality_tier="high"
    ),
    "llama-3.1-8b-instant": ModelCapabilities(
        provider="groq", model="llama-3.1-8b-instant",
        supports_structured_output=True, supports_vision=False, max_context_window=128000, quality_tier="fast"
    ),
    "qwen-2.5-32b": ModelCapabilities(
        provider="groq", model="qwen-2.5-32b",
        supports_structured_output=True, supports_vision=False, max_context_window=128000, quality_tier="standard"
    ),

    # Cloudflare
    "@cf/moonshotai/kimi-k2.6": ModelCapabilities(
        provider="cloudflare", model="@cf/moonshotai/kimi-k2.6",
        supports_structured_output=False, supports_vision=False, max_context_window=32000, quality_tier="standard"
    ),
    "@cf/meta/llama-3-8b-instruct": ModelCapabilities(
        provider="cloudflare", model="@cf/meta/llama-3-8b-instruct",
        supports_structured_output=True, supports_vision=False, max_context_window=8192, quality_tier="fast"
    ),

    # OpenRouter
    "deepseek/deepseek-chat": ModelCapabilities(
        provider="openrouter", model="deepseek/deepseek-chat",
        supports_structured_output=True, supports_vision=False, max_context_window=128000, quality_tier="high"
    )
}

def get_model_capabilities(provider: str, model: str) -> ModelCapabilities:
    """Lookup model capabilities, defaulting to basic capabilities if unknown."""
    # Attempt exact match or model-only match
    key = model
    if key.startswith(f"{provider}/"):
        key = key.split("/", 1)[1]
        
    return MODEL_CAPABILITIES_REGISTRY.get(key, ModelCapabilities(
        provider=provider, model=model
    ))
