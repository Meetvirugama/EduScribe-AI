"""
LLM Providers Package

Each module provides a concrete implementation of BaseProvider for
one integrated LLM provider. All providers communicate exclusively
through LiteLLM — no provider SDK is imported directly anywhere.

Providers registered in the four-tier waterfall (§15.1):
    Tier 1: Google (gemini), OpenRouter (deepseek-v3, qwen3)
    Tier 2: Cerebras (llama4, qwen3-32b), Groq (llama33, qwen3)
    Tier 3: Together AI (llama33-free, deepseek-r1-free), SambaNova, Mistral
    Tier 4: OpenRouter :free router, Groq llama-3.1-8b, Mistral nemo

LLD Reference: §15.1 The Four-Tier Waterfall, §15.3 Folder Structure
"""

from .google_provider import GoogleProvider
from .openrouter_provider import OpenRouterProvider
from .groq_provider import GroqProvider

__all__ = [
    "GoogleProvider",
    "OpenRouterProvider",
    "GroqProvider",
]
