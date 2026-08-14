import logging
import time
from typing import Any, Optional, List, Dict, Union
import litellm

from .key_manager import KeyManager
from .retry_manager import RetryManager
from .quota_tracker import QuotaTracker
from .providers.adapters import ProviderAdapterFactory
from .base_provider import ProviderTransientError, ProviderPermanentError
from .error_handler import ErrorHandler
from .pipeline import RequestContext, TaskType

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Decoupled pipeline orchestrator for embedding calls.
    Shares the resilience architecture (Fallback, Retry, Key Rotation) with LLMManager.
    """

    def __init__(
        self,
        quota_tracker: Optional[QuotaTracker] = None,
        key_manager: Optional[KeyManager] = None,
        retry_manager: Optional[RetryManager] = None,
    ) -> None:
        self.quota_tracker = quota_tracker or QuotaTracker()
        self.key_manager = key_manager or KeyManager()
        self.retry_manager = retry_manager or RetryManager()
        self.adapter_factory = ProviderAdapterFactory(self.key_manager)

        # Standard embedding fallback chain
        self.fallback_chain = [
            {"provider": "gemini", "model": "gemini/text-embedding-004"},
            {"provider": "cohere", "model": "cohere/embed-english-v3.0"},
            {"provider": "cloudflare",
             "model": "cloudflare/@cf/baai/bge-large-en-v1.5"}
        ]

    async def embed(
        self,
        text: Union[str, List[str]],
        **litellm_kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Executes a single Embedding request, falling back through the embedding chain.
        """
        context = RequestContext(
            task=TaskType.METADATA_EXTRACTION,
            messages=[],
            request_id="embed_" + str(time.time())[-6:]
        )

        async def _call_provider(prov: str, mod: str) -> Dict[str, Any]:
            api_key = self.key_manager.get_active_key(prov)
            adapter = self.adapter_factory.get_adapter(prov)
            provider_kwargs = adapter.prepare_request(prov, mod, api_key)
            call_kwargs = {**litellm_kwargs, **provider_kwargs}

            start_time = time.time()
            try:
                raw = await litellm.aembedding(
                    model=mod,
                    input=text,
                    api_key=api_key,
                    num_retries=0,
                    **call_kwargs,
                )

                latency = time.time() - start_time
                usage = raw.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                logger.info(
                    f"EMBED_REQUEST_SUCCESS | req_id={context.request_id} | "
                    f"provider={prov} | model={mod} | latency={latency:.2f}s | tokens={tokens}"
                )

                return raw

            except Exception as exc:
                ErrorHandler.handle_litellm_error(exc, prov, mod, context, self.key_manager, api_key)
                raise  # Unreachable due to ErrorHandler, but keeps type checker happy

        last_error = None
        for entry in self.fallback_chain:
            provider = entry["provider"]
            model = entry["model"]

            if not self.quota_tracker.has_quota(provider):
                logger.info(
                    f"Skipping {provider} embedding due to quota exhaustion.")
                continue

            try:
                # Wrap with retry manager
                return await self.retry_manager.execute_with_retry(
                    provider,
                    _call_provider,
                    provider,
                    model
                )
            except ProviderTransientError as exc:
                logger.warning(
                    f"Embedding transient failure on {provider}, trying next fallback. Error: {exc}")
                last_error = exc
            except ProviderPermanentError as exc:
                logger.warning(
                    f"Embedding permanent failure on {provider}, skipping provider. Error: {exc}")
                last_error = exc
            except Exception as exc: # Catch RetryError from tenacity
                logger.warning(
                    f"Embedding failed after all retries on {provider}, trying next fallback. Error: {exc}")
                last_error = exc

        raise RuntimeError(
            f"All embedding providers exhausted. Last error: {last_error}")
