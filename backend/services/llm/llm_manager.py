"""
llm_manager.py — Tier Waterfall Orchestrator

The central orchestrator for all LLM calls in EduScribe AI.
No component outside of services/llm/ ever calls an LLM directly —
every request flows through this class.

Call flow (LLD §15.4 Internal Workflow):
    Business Logic
        → LLMManager.generate()
        → model_selector.get_model_config(task)
        → quota_tracker.has_quota(primary)
        → key_manager.get_active_key(provider)
        → LiteLLM (via fallback_manager + retry_manager)
        → response_parser.parse()
        → PydanticAI schema validation (caller's responsibility)
        → Structured Response → calling service

LLD Reference: §15 LLM Provider Architecture
               §15.4 Internal Workflow
               §16 LiteLLM
               §16.3 Usage in Application Code
               §18 Model Routing
               §18.3 Routing Decision Workflow
"""

import logging
import os
from typing import Any, Optional

import litellm

from .model_selector import TaskType, ModelConfig, get_model_config
from .key_manager import KeyManager
from .quota_tracker import QuotaTracker
from .retry_manager import RetryManager
from .fallback_manager import FallbackManager, AllProvidersExhaustedError
from .response_parser import ResponseParser, ResponseParseError
from .base_provider import ProviderTransientError, ProviderPermanentError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LiteLLM Proxy URL
# When the LiteLLM proxy is running (Docker, localhost, or sidecar),
# route all calls through it. The proxy handles key rotation,
# budget tracking, and fallback at the infrastructure level.
# LLD Reference: §16.2 LiteLLM Proxy (Self-Hosted Gateway)
# ---------------------------------------------------------------------------
LITELLM_PROXY_URL: Optional[str] = os.environ.get("LITELLM_PROXY_URL")


class LLMManager:
    """
    Tier waterfall orchestrator for all LLM calls.

    Responsibilities (LLD §15.4):
        - Select the best provider and model for the current task (§18).
        - Check quota availability before making a call (§15.4).
        - Delegate key selection to KeyManager (§21).
        - Execute the call through LiteLLM (§16).
        - Apply exponential-backoff retry via RetryManager (§19).
        - Cascade to the next provider on failure via FallbackManager (§20).
        - Normalise the raw response via ResponseParser.
        - Record request statistics against QuotaTracker.

    All downstream services (notes_service, quiz_service, rag_service, etc.)
    call LLMManager.generate() — they never import litellm or any provider
    SDK directly. This enforces the "mandatory provider abstraction" design
    commitment (LLD §24.2, §15).

    Usage:
        manager = LLMManager()

        response = await manager.generate(
            task=TaskType.TOPIC_DETECTION,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
        content: str = response["content"]
    """

    def __init__(
        self,
        quota_tracker: Optional[QuotaTracker] = None,
        key_manager: Optional[KeyManager] = None,
        retry_manager: Optional[RetryManager] = None,
        fallback_manager: Optional[FallbackManager] = None,
        response_parser: Optional[ResponseParser] = None,
    ) -> None:
        """
        All sub-managers are injectable for testing and can be provided
        externally; sensible defaults are created if not supplied.
        """
        self.quota_tracker   = quota_tracker   or QuotaTracker()
        self.key_manager     = key_manager     or KeyManager()
        self.retry_manager   = retry_manager   or RetryManager()
        self.fallback_manager = fallback_manager or FallbackManager()
        self.response_parser = response_parser or ResponseParser()

        # Configure LiteLLM to route through the proxy if available
        if LITELLM_PROXY_URL:
            litellm.api_base = LITELLM_PROXY_URL
            logger.info("llm_manager: routing all calls through LiteLLM proxy at %s", LITELLM_PROXY_URL)
        else:
            logger.info("llm_manager: no LiteLLM proxy configured — calling provider APIs directly")

    # ---------------------------------------------------------------------------
    # Primary entry point for all LLM calls
    # ---------------------------------------------------------------------------

    async def generate(
        self,
        task: TaskType,
        messages: list[dict[str, str]],
        *,
        override_model: Optional[str] = None,
        override_temperature: Optional[float] = None,
        override_max_tokens: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
        **litellm_kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute an LLM call for the given task type, applying the full
        three-layer resilience architecture (key rotation → retry → fallback).

        Args:
            task:                  Task type — used to look up the routing table.
            messages:              OpenAI-format message list.
            override_model:        Bypass the routing table and use this model ID.
            override_temperature:  Override the routing-table temperature.
            override_max_tokens:   Override the routing-table max_tokens.
            metadata:              Passed to Langfuse via LiteLLM callback for
                                   observability (LLD §16.2 LiteLLM Proxy).
            **litellm_kwargs:      Any additional litellm.acompletion() parameters.

        Returns:
            Normalised response dict from ResponseParser.parse().

        Raises:
            AllProvidersExhaustedError: If the entire four-tier fallback chain fails.
        """
        config: ModelConfig = get_model_config(task)

        temperature = override_temperature if override_temperature is not None else config.temperature
        max_tokens  = override_max_tokens  if override_max_tokens  is not None else config.max_tokens

        # Determine the starting model
        if override_model:
            starting_model    = override_model
            starting_provider = self._provider_from_model(override_model)
        else:
            # Check quota on primary → secondary → emergency
            starting_model, starting_provider = self._select_starting_model(config)

        logger.info(
            "llm_manager: task=%s model=%s temp=%.2f max_tokens=%d",
            task.value,
            starting_model,
            temperature,
            max_tokens,
        )

        # Build the LiteLLM call function
        async def _call_provider(provider: str, model: str) -> dict[str, Any]:
            api_key = self.key_manager.get_active_key(provider)

            try:
                raw = await litellm.acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key,
                    metadata=metadata or {"task": task.value},
                    num_retries=0,         # retries handled by retry_manager
                    **litellm_kwargs,
                )
                return self.response_parser.parse(raw, provider=provider)

            except litellm.RateLimitError as exc:
                # 429 — rate limit: transient, retry with backoff
                if not self.key_manager.mark_key_exhausted(provider):
                    # All keys exhausted — re-raise as transient to trigger fallback
                    raise ProviderTransientError(
                        f"All keys exhausted for '{provider}': {exc}"
                    ) from exc
                raise ProviderTransientError(str(exc)) from exc

            except litellm.Timeout as exc:
                raise ProviderTransientError(str(exc)) from exc

            except litellm.ServiceUnavailableError as exc:
                raise ProviderTransientError(str(exc)) from exc

            except litellm.AuthenticationError as exc:
                # 401/403 — bad API key: permanent, no retry
                raise ProviderPermanentError(str(exc)) from exc

            except litellm.BadRequestError as exc:
                # 400 — malformed request: permanent, no retry
                raise ProviderPermanentError(str(exc)) from exc

            except ResponseParseError as exc:
                # Treat parse failures as transient (response may have been malformed)
                raise ProviderTransientError(str(exc)) from exc

        # Execute through the fallback waterfall
        return await self.fallback_manager.execute_with_fallback(
            call_fn=_call_provider,
            quota_tracker=self.quota_tracker,
            key_manager=self.key_manager,
            retry_manager=self.retry_manager,
            preferred_provider=starting_provider,
            preferred_model=starting_model,
        )

    # ---------------------------------------------------------------------------
    # Convenience helpers for common task types
    # ---------------------------------------------------------------------------

    async def analyse_lecture(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.LECTURE_ANALYSIS."""
        return await self.generate(TaskType.LECTURE_ANALYSIS, messages)

    async def detect_topics(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.TOPIC_DETECTION."""
        return await self.generate(TaskType.TOPIC_DETECTION, messages)

    async def detect_subtopics(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.SUBTOPIC_DETECTION."""
        return await self.generate(TaskType.SUBTOPIC_DETECTION, messages)

    async def generate_notes(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.DETAILED_NOTES."""
        return await self.generate(TaskType.DETAILED_NOTES, messages)

    async def generate_quiz(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.QUIZ_GENERATION."""
        return await self.generate(TaskType.QUIZ_GENERATION, messages)

    async def generate_flashcards(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.FLASHCARD_GENERATION."""
        return await self.generate(TaskType.FLASHCARD_GENERATION, messages)

    async def answer_rag_query(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.RAG_ANSWERING."""
        return await self.generate(TaskType.RAG_ANSWERING, messages)

    async def correct_ocr(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.OCR_CORRECTION."""
        return await self.generate(TaskType.OCR_CORRECTION, messages)

    async def extract_concepts(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.CONCEPT_EXTRACTION."""
        return await self.generate(TaskType.CONCEPT_EXTRACTION, messages)

    async def extract_keywords(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.KEYWORD_EXTRACTION."""
        return await self.generate(TaskType.KEYWORD_EXTRACTION, messages)

    async def detect_learning_objectives(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.LEARNING_OBJECTIVE_DETECTION."""
        return await self.generate(TaskType.LEARNING_OBJECTIVE_DETECTION, messages)

    async def detect_prerequisites(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.PREREQUISITE_DETECTION."""
        return await self.generate(TaskType.PREREQUISITE_DETECTION, messages)

    async def classify_difficulty(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.DIFFICULTY_CLASSIFICATION."""
        return await self.generate(TaskType.DIFFICULTY_CLASSIFICATION, messages)

    async def generate_definitions(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.DEFINITION_GENERATION."""
        return await self.generate(TaskType.DEFINITION_GENERATION, messages)

    async def generate_step_by_step(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.STEP_BY_STEP_EXPLANATION."""
        return await self.generate(TaskType.STEP_BY_STEP_EXPLANATION, messages)

    async def detect_misconceptions(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.MISCONCEPTION_DETECTION."""
        return await self.generate(TaskType.MISCONCEPTION_DETECTION, messages)

    async def detect_edge_cases(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.EDGE_CASE_DETECTION."""
        return await self.generate(TaskType.EDGE_CASE_DETECTION, messages)

    async def generate_learning_path(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.LEARNING_PATH_RECOMMENDATION."""
        return await self.generate(TaskType.LEARNING_PATH_RECOMMENDATION, messages)

    async def generate_real_world_applications(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.REAL_WORLD_APPLICATIONS."""
        return await self.generate(TaskType.REAL_WORLD_APPLICATIONS, messages)

    async def verify_facts(self, messages: list[dict]) -> dict:
        """Shortcut for TaskType.FACT_VERIFICATION."""
        return await self.generate(TaskType.FACT_VERIFICATION, messages)

    async def generate_embeddings(self, text: str) -> list[float]:
        """
        Generate vector embeddings for a given string using litellm.
        We default to gemini-embedding-exp-03-07 or similar if proxy not configured.
        """
        # For V1, we simply call litellm.aembedding. In a full system, 
        # this would route via a specific Embeddings config in ModelSelector.
        try:
            # We use text-embedding-3-small via openrouter or directly gemini embeddings
            # We'll rely on litellm's default fallback or a specific model if needed
            model_name = "gemini/text-embedding-004"
            api_key = self.key_manager.get_active_key("gemini")
            response = await litellm.aembedding(
                model=model_name,
                input=text,
                api_key=api_key
            )
            return response.data[0]["embedding"]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return []

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _select_starting_model(self, config: ModelConfig) -> tuple[str, str]:
        """
        Walk primary → secondary → emergency and return the first model
        whose provider has remaining quota.

        LLD Reference: §18.3 Routing Decision Workflow
        """
        candidates = [
            config.primary,
            config.secondary,
            config.emergency,
        ]
        for model_id in candidates:
            provider = self._provider_from_model(model_id)
            if self.quota_tracker.has_quota(provider):
                return model_id, provider

        # All three have no quota — start from primary anyway and let
        # the fallback chain handle degradation
        logger.warning(
            "llm_manager: no preferred model has quota; starting from primary '%s'",
            config.primary,
        )
        return config.primary, self._provider_from_model(config.primary)

    @staticmethod
    def _provider_from_model(model_id: str) -> str:
        """
        Infer the provider name from a LiteLLM model ID / proxy alias.

        Handles the following provider ID schemes:
          - gemini/...       → gemini
          - cohere/...       → cohere
          - cloudflare/...   → cloudflare
          - groq/...         → groq
          - openrouter/...   → openrouter
          - jina/...         → jina
          - huggingface/...  → huggingface
          - Bare aliases     → inferred by keyword

        LLD Reference: §15.2 Integrated Provider Reference
        """
        model_lower = model_id.lower()

        # Explicit provider-prefixed IDs (standard LiteLLM format)
        if model_lower.startswith("gemini/"):
            return "gemini"
        if model_lower.startswith("cohere/"):
            return "cohere"
        if model_lower.startswith("cloudflare/") or model_lower.startswith("@cf/"):
            return "cloudflare"
        if model_lower.startswith("groq/"):
            return "groq"
        if model_lower.startswith("openrouter/") or ":free" in model_lower:
            return "openrouter"
        if model_lower.startswith("jina/"):
            return "jina"
        if model_lower.startswith("huggingface/") or model_lower.startswith("hf/"):
            return "huggingface"
        if model_lower.startswith("github/"):
            return "github"

        # Legacy bare aliases (proxy aliases without prefix)
        if "gemini" in model_lower or "flash" in model_lower:
            return "gemini"
        if "command" in model_lower or "cohere" in model_lower:
            return "cohere"
        if model_lower.startswith("groq") or "llama33" in model_lower or "llama8b" in model_lower:
            return "groq"
        if "deepseek" in model_lower or "qwen" in model_lower:
            return "openrouter"
        if "kimi" in model_lower or "mistral-small" in model_lower or "moondream" in model_lower:
            return "cloudflare"

        return "unknown"
