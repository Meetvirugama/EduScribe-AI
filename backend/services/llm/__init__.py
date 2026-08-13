"""
LLM Services Package — EduScribe AI

The single, centralised LLM access layer. No module outside this
package ever calls an LLM provider directly — mandatory provider
abstraction (LLD §24.2).

Call flow:
    Business Logic
        → LLMManager.generate(task, messages)
        → model_selector.get_model_config(task)
        → quota_tracker.has_quota(provider)
        → key_manager.get_active_key(provider)
        → retry_manager (Tenacity exponential backoff)
        → fallback_manager (four-tier waterfall)
        → LiteLLM → Provider API
        → response_parser.parse()
        → Structured Response

LLD Reference: §15 LLM Provider Architecture
               §15.4 Internal Workflow
               §16 LiteLLM
               §17 PydanticAI (schemas in response_parser.py)
               §18 Model Routing
               §19 Retry Strategy
               §20 Fallback Strategy
               §21 API Key Rotation
"""

from .llm_manager import LLMManager
from .model_selector import TaskType
from .fallback_manager import AllProvidersExhaustedError

__all__ = [
    "LLMManager",
    "TaskType",
    "AllProvidersExhaustedError",
]
