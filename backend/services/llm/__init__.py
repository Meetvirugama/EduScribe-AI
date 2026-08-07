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
from .model_selector import (
    TaskType,
    ModelConfig,
    get_model_config,
    get_primary_model,
    get_secondary_model,
    get_emergency_model,
    list_all_task_types,
    get_tasks_by_phase,
    ROUTING_TABLE,
)
from .base_provider import BaseProvider, ProviderTransientError, ProviderPermanentError
from .key_manager import KeyManager
from .quota_tracker import QuotaTracker
from .retry_manager import RetryManager
from .fallback_manager import FallbackManager, AllProvidersExhaustedError, FALLBACK_CHAIN
from .validation import (
    RawResponseParser,
    ResponseParseError,
)
from .validation.schemas.core import (
    LectureAnalysis,
    TopicList,
    Topic,
    SubtopicList,
    KnowledgeGap,
    SubtopicExplanation,
    ExampleSet,
    QuizSet,
    QuizQuestion,
    FlashcardSet,
    Flashcard,
    MindMap,
)

__all__ = [
    # Orchestrator — primary entry point
    "LLMManager",

    # Task routing
    "TaskType",
    "ModelConfig",
    "ROUTING_TABLE",
    "get_model_config",
    "get_primary_model",
    "get_secondary_model",
    "get_emergency_model",
    "list_all_task_types",
    "get_tasks_by_phase",

    # Provider base
    "BaseProvider",
    "ProviderTransientError",
    "ProviderPermanentError",

    # Sub-managers
    "KeyManager",
    "QuotaTracker",
    "RetryManager",
    "FallbackManager",
    "AllProvidersExhaustedError",
    "FALLBACK_CHAIN",

    # Response layer
    "RawResponseParser",
    "ResponseParseError",

    # PydanticAI schemas (§17.2)
    "LectureAnalysis",
    "TopicList",
    "Topic",
    "SubtopicList",
    "KnowledgeGap",
    "SubtopicExplanation",
    "ExampleSet",
    "QuizSet",
    "QuizQuestion",
    "FlashcardSet",
    "Flashcard",
    "MindMap",
]

