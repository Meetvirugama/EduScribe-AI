import logging
from typing import Any, Dict
from abc import ABC, abstractmethod
from ..key_manager import KeyManager

logger = logging.getLogger(__name__)

class BaseProviderAdapter(ABC):
    """
    Abstract base class for provider adapters.
    Adapters are responsible for preparing provider-specific kwargs for LiteLLM
    (e.g., custom api_base, custom headers) without polluting the core orchestrator.
    """
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        
    @abstractmethod
    def prepare_request(self, provider: str, model: str, api_key: str) -> Dict[str, Any]:
        pass


class CloudflareAdapter(BaseProviderAdapter):
    def prepare_request(self, provider: str, model: str, api_key: str) -> Dict[str, Any]:
        kwargs = {}
        account_id = self.key_manager.get_active_account_id(provider, api_key)
        if account_id:
            kwargs["api_base"] = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/"
        else:
            logger.warning("CloudflareAdapter: No account_id found for API key in KeyManager. Relying on LiteLLM default environment variables.")
        return kwargs


class DefaultAdapter(BaseProviderAdapter):
    """Fallback adapter for providers that do not need special LiteLLM kwargs."""
    def prepare_request(self, provider: str, model: str, api_key: str) -> Dict[str, Any]:
        return {}


class ProviderAdapterFactory:
    """Factory to fetch the correct adapter for a given provider."""
    def __init__(self, key_manager: KeyManager):
        self._adapters: Dict[str, BaseProviderAdapter] = {
            "cloudflare": CloudflareAdapter(key_manager),
            "default": DefaultAdapter(key_manager)
        }
        
    def get_adapter(self, provider: str) -> BaseProviderAdapter:
        provider = provider.strip().lower() if provider else "default"
        return self._adapters.get(provider, self._adapters["default"])
