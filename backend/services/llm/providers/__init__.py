"""
LLM Providers Package

This package exposes ProviderAdapterFactory and adapters which handle
provider-specific LiteLLM kwargs configurations (e.g. Cloudflare api_base).
All actual LLM execution is handled directly by LLMManager using litellm.acompletion().
"""

from .adapters import ProviderAdapterFactory, BaseProviderAdapter, DefaultAdapter, CloudflareAdapter

__all__ = [
    "ProviderAdapterFactory",
    "BaseProviderAdapter",
    "DefaultAdapter",
    "CloudflareAdapter",
]
