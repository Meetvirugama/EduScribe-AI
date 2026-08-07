"""
key_manager.py — Per-Provider API Key Rotation

Cycles through all registered API keys for a provider before declaring
that provider exhausted. Switching keys within the same provider is
always preferred over switching providers, because a key switch
preserves the currently selected model's quality characteristics,
whereas a provider switch changes the underlying model entirely.

LLD Reference: §21 API Key Rotation
               §21.3 Detailed Explanation
               §21.4 Internal Workflow

Three-layer resilience architecture (§21.3):
    1. API Key Rotation (§21)  — try all keys on current provider
            ↓ all keys exhausted
    2. Retry Strategy (§19)    — retry with exponential backoff on current provider
            ↓ all retries exhausted
    3. Fallback Strategy (§20) — switch to next provider in sequence

Key rotation example (§21.3):
    Google: Key 1 → Quota Full → Key 2 → Quota Full → Key 3 → Quota Full
            → Switch Provider (Fallback Strategy §20)
"""

import os
import logging
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Per-provider API key rotation manager.

    Maintains an ordered list of API keys for each integrated provider
    and cycles through them round-robin when a key's quota is exhausted.
    Only after every key for a given provider is exhausted does the
    system escalate to the Fallback Strategy (switching providers).

    Thread-safe: uses a per-provider lock so multiple Celery workers
    can safely rotate keys concurrently without racing.

    LLD Reference: §21 API Key Rotation
    """

    # ---------------------------------------------------------------------------
    # Registered providers and their environment-variable names.
    # ---------------------------------------------------------------------------
    # Provider → Ordered list of env-var names for that provider's API keys.
    # Keys are tried in order; exhausted keys are skipped until quota resets.
    # Naming matches backend/.env exactly — update both files together.
    # Architecture: AI Router → LLM Router | Embedding Router | Vision Router
    # ---------------------------------------------------------------------------
    _PROVIDER_ENV_VARS: dict[str, list[str]] = {
        # LLM Router — Tier 2: High-Speed Free (14,400 RPD per key)
        # Key purposes: K1=DeepSeek-R1(Math), K2=Llama33(Notes), K3=Qwen(Code),
        #               K4=Whisper(Speech), K5=Backup
        "groq": [
            "GROQ_API_KEY_1",
            "GROQ_API_KEY_2",
            "GROQ_API_KEY_3",
            "GROQ_API_KEY_4",
            "GROQ_API_KEY_5",
        ],
        # LLM Router — Tier 1: Premium Free (1M context, OCR, multimodal)
        # Key purposes: K1=NoteGen, K2=OCR+Vision, K3=HTML+Markdown, K4=Backup
        "gemini": [
            "GEMINI_API_KEY_1",
            "GEMINI_API_KEY_2",
            "GEMINI_API_KEY_3",
            "GEMINI_API_KEY_4",
        ],
        # LLM Router — Tier 1 & 3: OpenRouter free models
        # Key purposes: K1=DeepSeekV3, K2=Qwen, K3=Llama, K4=Mistral, K5=Emergency
        "openrouter": [
            "OPENROUTER_API_KEY_1",
            "OPENROUTER_API_KEY_2",
            "OPENROUTER_API_KEY_3",
            "OPENROUTER_API_KEY_4",
            "OPENROUTER_API_KEY_5",
        ],
        # Embedding Router — Primary (BGE-M3, e5-Mistral, Jina-via-HF)
        # Key purposes: K1=BGE-M3, K2=e5-Mistral, K3=Jina-via-HF, K4=Research
        "huggingface": [
            "HF_API_KEY_1",
            "HF_API_KEY_2",
            "HF_API_KEY_3",
            "HF_API_KEY_4",
        ],
        # Embedding Router — RAG pipeline (Transcript→Chunking→Jina→Qdrant)
        "jina": [
            "JINA_API_KEY",
        ],
        # Embedding Router — Reranking + Semantic Search
        # Key purposes: K1=Reranking, K2=Embeddings, K3=Search, K4=Backup, K5=HighTraffic
        "cohere": [
            "COHERE_API_KEY_1",
            "COHERE_API_KEY_2",
            "COHERE_API_KEY_3",
            "COHERE_API_KEY_4",
            "COHERE_API_KEY_5",
        ],
        # Dev/Test ONLY — NOT for production (benchmarking, A/B testing, CI/CD)
        "github": [
            "GITHUB_MODELS_TOKEN",
        ],
        # Vision Router / Edge — Cloudflare Workers AI
        # Key purposes: K1=Llama(edge), K2=BGE-embed, K3=Whisper, K4=EdgeChat, K5=Backup
        "cloudflare": [
            "CLOUDFLARE_API_KEY_1",
            "CLOUDFLARE_API_KEY_2",
            "CLOUDFLARE_API_KEY_3",
            "CLOUDFLARE_API_KEY_4",
            "CLOUDFLARE_API_KEY_5",
        ],
    }


    def __init__(self) -> None:
        # provider_name → [list of available keys]
        self._keys: dict[str, list[str]] = {}
        # provider_name → current index into the key list
        self._current_index: dict[str, int] = {}
        # provider_name → set of exhausted key indices
        self._exhausted: dict[str, set[int]] = {}
        # per-provider threading lock
        self._locks: dict[str, Lock] = {}

        self._load_keys()

    def _load_keys(self) -> None:
        """
        Load all API keys from environment variables.
        Keys that are missing or empty are silently skipped.
        """
        for provider, env_vars in self._PROVIDER_ENV_VARS.items():
            loaded: list[str] = []
            for env_var in env_vars:
                value = os.environ.get(env_var, "").strip()
                if value:
                    loaded.append(value)
                else:
                    logger.debug(
                        "key_manager: env var %s not set for provider %s — skipped",
                        env_var,
                        provider,
                    )

            self._keys[provider] = loaded
            self._current_index[provider] = 0
            self._exhausted[provider] = set()
            self._locks[provider] = Lock()

            if loaded:
                logger.info(
                    "key_manager: loaded %d key(s) for provider '%s'",
                    len(loaded),
                    provider,
                )
            else:
                logger.warning(
                    "key_manager: no API keys found for provider '%s'",
                    provider,
                )

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def get_active_key(self, provider: str) -> Optional[str]:
        """
        Return the current active API key for the given provider.

        Returns None if the provider is unknown or has no configured keys.
        Does NOT advance the rotation index — call mark_key_exhausted() when
        a key returns a quota error.

        LLD Reference: §21.4 Internal Workflow step B → "Use Key N"
        """
        keys = self._keys.get(provider)
        if not keys:
            return None

        with self._locks[provider]:
            idx = self._current_index[provider]
            if idx < len(keys):
                return keys[idx]
            return None  # all keys exhausted

    def mark_key_exhausted(self, provider: str) -> bool:
        """
        Mark the current key as quota-exhausted and advance to the next key.

        Returns:
            True  — a next key is available; the caller should retry with it.
            False — all keys are exhausted; the caller must escalate to
                    the Fallback Strategy (switch provider).

        LLD Reference: §21.4 Internal Workflow — Key N → Quota Full → Key N+1
        """
        keys = self._keys.get(provider)
        if not keys:
            return False

        with self._locks[provider]:
            current_idx = self._current_index[provider]
            self._exhausted[provider].add(current_idx)

            # Find the next non-exhausted key
            for next_idx in range(current_idx + 1, len(keys)):
                if next_idx not in self._exhausted[provider]:
                    self._current_index[provider] = next_idx
                    logger.info(
                        "key_manager: key %d exhausted for '%s' → rotating to key %d",
                        current_idx + 1,
                        provider,
                        next_idx + 1,
                    )
                    return True  # next key available

            # All keys exhausted → escalate to Fallback Strategy
            logger.warning(
                "key_manager: all %d key(s) exhausted for provider '%s' "
                "→ escalating to Fallback Strategy",
                len(keys),
                provider,
            )
            return False

    def all_keys_exhausted(self, provider: str) -> bool:
        """
        Return True if every configured key for this provider has been
        marked as exhausted. Signals that the Fallback Strategy should
        switch providers entirely.

        LLD Reference: §21.4 Internal Workflow — "All keys exhausted → Switch Provider"
        """
        keys = self._keys.get(provider)
        if not keys:
            return True

        with self._locks[provider]:
            return len(self._exhausted[provider]) >= len(keys)

    def reset_provider_keys(self, provider: str) -> None:
        """
        Reset exhaustion state for a provider (e.g., after a daily quota reset).
        Typically called at midnight UTC when most free-tier quotas refresh.

        LLD Reference: §15.6 — "quotas reset at midnight UTC"
        """
        with self._locks[provider]:
            self._current_index[provider] = 0
            self._exhausted[provider] = set()
        logger.info("key_manager: reset all keys for provider '%s'", provider)

    def get_key_count(self, provider: str) -> int:
        """Return the number of configured keys for a provider."""
        return len(self._keys.get(provider, []))

    def get_available_providers(self) -> list[str]:
        """Return the list of providers that have at least one configured key."""
        return [p for p, keys in self._keys.items() if keys]
