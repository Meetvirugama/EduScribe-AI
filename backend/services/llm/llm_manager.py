"""
llm_manager.py — Pipeline Orchestrator

The central orchestrator for all LLM calls in EduScribe AI.
Implements a clean pipeline architecture separating context analysis,
capability detection, model selection, execution, and metric collection.

LLD Reference: §15 LLM Provider Architecture
"""

import logging
import os
import time
import uuid
from typing import Any, AsyncGenerator, Optional

import litellm

from .model_selector import TaskType, ModelConfig, get_model_config
from .key_manager import KeyManager
from .quota_tracker import QuotaTracker
from .retry_manager import RetryManager
from .fallback_manager import FallbackManager
from pydantic import ValidationError
from .validation import (
    RawResponseParser,
    JSONExtractor,
    SchemaRegistry,
    ResponseParseError,
    JSONExtractionError,
    SchemaValidationError,
    BaseLLMOutput
)
from .base_provider import ProviderTransientError

from .pipeline import RequestContext, CapabilityDetector, RequestCache, MetricsRecorder
from .error_handler import ErrorHandler
from .providers.adapters import ProviderAdapterFactory
from .embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)
LITELLM_PROXY_URL: Optional[str] = os.environ.get("LITELLM_PROXY_URL")

class LLMManager:
    """
    Decoupled pipeline orchestrator for all LLM calls.
    """

    def __init__(
        self,
        quota_tracker: Optional[QuotaTracker] = None,
        key_manager: Optional[KeyManager] = None,
        retry_manager: Optional[RetryManager] = None,
        fallback_manager: Optional[FallbackManager] = None,
        # Validation is now static via the validation package
        request_cache: Optional[RequestCache] = None,
    ) -> None:
        self.quota_tracker   = quota_tracker   or QuotaTracker()
        self.key_manager     = key_manager     or KeyManager()
        self.retry_manager   = retry_manager   or RetryManager()
        self.fallback_manager = fallback_manager or FallbackManager()
        # validation package methods are static
        self.request_cache   = request_cache   or RequestCache()
        self.adapter_factory = ProviderAdapterFactory(self.key_manager)

        if LITELLM_PROXY_URL:
            litellm.api_base = LITELLM_PROXY_URL
            logger.info("llm_manager: routing through LiteLLM proxy at %s", LITELLM_PROXY_URL)

        # CRITICAL-007: Lazily created EmbeddingManager shared by embed() calls.
        # EmbeddingManager reuses the same resilience infrastructure (key rotation,
        # quota tracking) as LLMManager to avoid redundant initialisation.
        self._embedding_manager: Optional[EmbeddingManager] = None

    def _select_starting_model(self, config: ModelConfig) -> tuple[str, str]:
        prim_prov = self._provider_from_model(config.primary)
        if self.quota_tracker.has_quota(prim_prov):
            return config.primary, prim_prov
            
        sec_prov = self._provider_from_model(config.secondary)
        if self.quota_tracker.has_quota(sec_prov):
            return config.secondary, sec_prov
            
        em_prov = self._provider_from_model(config.emergency)
        return config.emergency, em_prov

    def _provider_from_model(self, model: str) -> str:
        model_lower = model.lower()
        if model_lower.startswith("cloudflare/") or model_lower.startswith("@cf/"): return "cloudflare"
        if model_lower.startswith("gemini"): return "gemini"
        if model_lower.startswith("openrouter/"): return "openrouter"
        if model_lower.startswith("groq/"): return "groq"
        if model_lower.startswith("cohere/"): return "cohere"
        return model_lower.split("/")[0]

    async def embed(
        self,
        text,
        **kwargs,
    ):
        """
        Generate embeddings by delegating to the shared EmbeddingManager.

        CRITICAL-007: This method was previously missing entirely, causing an
        AttributeError in rag/pipeline.py and rag/embedding_store.py that
        silently killed the entire RAG pipeline (search always returned []).

        The EmbeddingManager is lazily created on first call and reused
        across subsequent calls within the same LLMManager instance.
        """
        if self._embedding_manager is None:
            self._embedding_manager = EmbeddingManager(
                quota_tracker=self.quota_tracker,
                key_manager=self.key_manager,
                retry_manager=self.retry_manager,
            )
        return await self._embedding_manager.embed(text, **kwargs)

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
        Executes a single LLM request through the pipeline.
        """
        # 1. Pipeline Stage: Request Context Initialization
        config = get_model_config(task)
        temp = override_temperature if override_temperature is not None else config.temperature
        max_t = override_max_tokens if override_max_tokens is not None else config.max_tokens
        
        context = RequestContext(
            task=task,
            messages=messages,
            temperature=temp,
            max_tokens=max_t,
            metadata=metadata or {},
            request_id=str(uuid.uuid4())[:8]
        )
        
        # 2. Pipeline Stage: Capability Detection
        response_format = litellm_kwargs.get("response_format", {}).get("type", "text")
        context.capabilities = CapabilityDetector.detect(messages, expected_output_format=response_format)
        
        # 3. Pipeline Stage: Context Analyzer
        if override_model:
            starting_model = override_model
            starting_provider = self._provider_from_model(override_model)
        else:
            starting_model, starting_provider = self._select_starting_model(config)
            
        try:
            prompt_tokens = litellm.token_counter(model=starting_model, messages=messages)
            context.estimated_tokens = prompt_tokens
            context.min_context_window = prompt_tokens + context.max_tokens
        except Exception as e:
            logger.debug(f"token_counter failed, defaulting context requirement to 0: {e}")
            context.min_context_window = 0

        # 4. Pipeline Stage: Request Cache
        cached_response = self.request_cache.get(context)
        if cached_response:
            logger.info(f"LLM_CACHE_HIT | req_id={context.request_id} | task={task.value}")
            return cached_response

        # 5. Pipeline Stage: Execution Closure
        async def _call_provider(provider: str, model: str) -> dict[str, Any]:
            api_key = self.key_manager.get_active_key(provider)
            adapter = self.adapter_factory.get_adapter(provider)
            provider_kwargs = adapter.prepare_request(provider, model, api_key)
            
            call_kwargs = {**litellm_kwargs, **provider_kwargs}
            start_time = time.time()
            
            try:
                raw = await litellm.acompletion(
                    model=model,
                    messages=context.messages,
                    temperature=context.temperature,
                    max_tokens=context.max_tokens,
                    api_key=api_key,
                    metadata=context.metadata,
                    num_retries=0, 
                    **call_kwargs,
                )
                
                # 6. Pipeline Stage: Raw Response Parsing
                parsed = RawResponseParser.parse(raw, provider=provider)
                
                # 7. Pipeline Stage: Metrics Recorder
                latency = time.time() - start_time
                usage = parsed.get("usage", {})
                MetricsRecorder.record(context, provider, model, latency, usage)
                
                # 8. Pipeline Stage: JSON Extraction & Pydantic Validation
                schema_cls = SchemaRegistry.get_schema(task)
                
                # If the schema is GenericTextOutput, skip JSON extraction
                if schema_cls.__name__ == "GenericTextOutput":
                    return schema_cls(
                        text=parsed["content"],
                        provider=provider,
                        model=model,
                        latency=latency,
                        total_tokens=usage.get("total_tokens", 0)
                    )
                
                try:
                    # Attempt to extract JSON (will repair if needed)
                    json_data = JSONExtractor.extract_and_repair(parsed["content"])
                except JSONExtractionError as e:
                    logger.warning(f"LLM_JSON_ERROR | req_id={context.request_id} | provider={provider} | err={e}")
                    raise ProviderTransientError(str(e)) from e
                
                try:
                    # Validate against strict Pydantic schema
                    validated_obj = schema_cls.model_validate(json_data)
                    
                    # Inject metadata (since schema inherits from BaseLLMOutput)
                    # Use model_copy(update=...) for frozen models
                    if hasattr(validated_obj, "model_copy"):
                        validated_obj = validated_obj.model_copy(update={
                            "provider": provider,
                            "model": model,
                            "latency": latency,
                            "total_tokens": usage.get("total_tokens", 0)
                        })
                        
                    return validated_obj
                except ValidationError as e:
                    logger.warning(f"LLM_VALIDATION_ERROR | req_id={context.request_id} | provider={provider} | err={e}")
                    raise ProviderTransientError(f"Pydantic Validation Error: {e}") from e

            except ResponseParseError as exc:
                logger.warning(f"LLM_REQUEST_FAILED | req_id={context.request_id} | provider={provider} | reason=ResponseParseError")
                raise ProviderTransientError(str(exc)) from exc
            except Exception as exc:
                # 7. Pipeline Stage: Error Handling
                ErrorHandler.handle_litellm_error(exc, provider, model, context)
                raise  # ErrorHandler always raises the mapped exception

        # 8. Pipeline Stage: Fallback Orchestration
        final_response = await self.fallback_manager.execute_with_fallback(
            call_fn=_call_provider,
            quota_tracker=self.quota_tracker,
            key_manager=self.key_manager,
            retry_manager=self.retry_manager,
            preferred_provider=starting_provider,
            preferred_model=starting_model,
            required_vision=context.capabilities.requires_vision,
            min_context_window=context.min_context_window,
        )
        
        # 9. Pipeline Stage: Cache the result
        self.request_cache.set(context, final_response)
        
        return final_response

    async def generate_stream(
        self,
        task: TaskType,
        messages: list[dict[str, str]],
        *,
        override_model: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        """
        Executes a streaming request through the pipeline.
        Note: Caching and Fallback are bypassed for streams.
        """
        config = get_model_config(task)
        context = RequestContext(
            task=task,
            messages=messages,
            request_id=str(uuid.uuid4())[:8]
        )
        context.capabilities = CapabilityDetector.detect(messages)
        
        starting_model = override_model or self._select_starting_model(config)[0]
        starting_provider = self._provider_from_model(starting_model)
        
        api_key = self.key_manager.get_active_key(starting_provider)
        adapter = self.adapter_factory.get_adapter(starting_provider)
        provider_kwargs = adapter.prepare_request(starting_provider, starting_model, api_key)
        call_kwargs = {**kwargs, **provider_kwargs}
        
        try:
            response = await litellm.acompletion(
                model=starting_model,
                messages=context.messages,
                api_key=api_key,
                stream=True,
                num_retries=0,
                **call_kwargs,
            )
            async for chunk in response:
                yield chunk
        except Exception as exc:
            ErrorHandler.handle_litellm_error(exc, starting_provider, starting_model, context)
