"""
key_manager.py — Per-Provider API Key Rotation

Cycles through all registered API keys for a provider using round-robin.
Handles dynamic loading of API keys from the environment and 
intelligent cooldowns for temporary rate limits.

LLD Reference: §21 API Key Rotation
"""

import os
import re
import time
import logging
from dataclasses import dataclass
from threading import Lock
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class KeyMetadata:
    """Tracks the health and usage metadata of a single API key."""
    key: str
    account_id: Optional[str] = None
    last_used: float = 0.0
    failure_count: int = 0
    cooldown_until: float = 0.0
    exhausted: bool = False

    def is_healthy(self) -> bool:
        """A key is healthy if it's not permanently exhausted and not in cooldown."""
        if self.exhausted:
            return False
        if time.time() < self.cooldown_until:
            return False
        return True


class KeyManager:
    """
    Per-provider API key rotation manager.

    Maintains an ordered list of API keys for each integrated provider
    and cycles through them round-robin.
    """

    def __init__(self) -> None:
        # provider_name → list of KeyMetadata
        self._keys: Dict[str, List[KeyMetadata]] = {}
        # provider_name → current index into the key list (round-robin)
        self._current_index: Dict[str, int] = {}
        # per-provider threading lock
        self._locks: Dict[str, Lock] = {}

        self._load_keys()

    def _validate_key(self, provider: str, key: str) -> bool:
        """Validates key format based on provider to catch malformed keys early."""
        if not key:
            return False
        provider = provider.lower()
        if provider == "groq" and not key.startswith("gsk_"):
            return False
        if provider == "openrouter" and not key.startswith("sk-or-"):
            return False
        if provider in ("huggingface", "hf") and not key.startswith("hf_"):
            return False
        return True

    def _load_keys(self) -> None:
        """
        Dynamically loads all API keys from environment variables.
        Supports both PROVIDER_API_KEYS (comma-separated) and 
        PROVIDER_API_KEY_1 (numbered).
        """
        providers_found = set()
        
        # Scan os.environ for anything matching *_API_KEY*
        for env_key in os.environ.keys():
            env_key = env_key.upper()
            
            match_numbered = re.match(r'^([A-Z0-9]+)_API_KEY(?:_\d+)?$', env_key)
            if match_numbered:
                providers_found.add(match_numbered.group(1).lower())
                
            match_plural = re.match(r'^([A-Z0-9]+)_API_KEYS$', env_key)
            if match_plural:
                providers_found.add(match_plural.group(1).lower())

        for provider in providers_found:
            loaded_meta: List[KeyMetadata] = []
            
            # Special case for huggingface
            env_prefix = "HUGGINGFACE" if provider in ("huggingface", "hf") else provider.upper()
            actual_provider = "huggingface" if provider == "hf" else provider
            
            # 1. Check plural comma-separated format
            plural_var = f"{env_prefix}_API_KEYS"
            if plural_var in os.environ:
                keys = [k.strip() for k in os.environ[plural_var].split(",") if k.strip()]
                for k in keys:
                    if self._validate_key(actual_provider, k):
                        loaded_meta.append(KeyMetadata(key=k))
            
            # 2. Check numbered format
            for i in range(1, 20):
                single_var = f"{env_prefix}_API_KEY_{i}"
                if single_var in os.environ:
                    k = os.environ[single_var].strip()
                    if k and self._validate_key(actual_provider, k):
                        meta = KeyMetadata(key=k)
                        
                        # Handle Cloudflare Account IDs paired with keys
                        if actual_provider == "cloudflare":
                            acc_var = f"{env_prefix}_ACCOUNT_ID_{i}"
                            meta.account_id = os.environ.get(acc_var, "").strip()
                            
                        loaded_meta.append(meta)
            
            # 3. Check singular format without number
            single_var_no_num = f"{env_prefix}_API_KEY"
            if single_var_no_num in os.environ and plural_var not in os.environ:
                k = os.environ[single_var_no_num].strip()
                if k and self._validate_key(actual_provider, k):
                    if not any(m.key == k for m in loaded_meta):
                        loaded_meta.append(KeyMetadata(key=k))

            if loaded_meta:
                self._keys[actual_provider] = loaded_meta
                self._current_index[actual_provider] = 0
                self._locks[actual_provider] = Lock()
                logger.info(
                    "key_manager: loaded %d key(s) for provider '%s'",
                    len(loaded_meta),
                    actual_provider,
                )

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def get_active_key(self, provider: str) -> Optional[str]:
        """
        Return the next healthy API key for the given provider using round-robin.
        Automatically cycles to the next healthy key on every call.
        """
        keys = self._keys.get(provider)
        if not keys:
            return None

        with self._locks[provider]:
            start_idx = self._current_index[provider]
            for i in range(len(keys)):
                idx = (start_idx + i) % len(keys)
                meta = keys[idx]
                
                if meta.is_healthy():
                    meta.last_used = time.time()
                    # Advance for the next call to achieve round-robin load balancing
                    self._current_index[provider] = (idx + 1) % len(keys)
                    return meta.key

            return None  # all keys exhausted or in cooldown

    def get_active_account_id(self, provider: str, key: str) -> Optional[str]:
        """Return the associated account_id for a specific key (e.g. Cloudflare)."""
        keys = self._keys.get(provider)
        if not keys:
            return None
        for meta in keys:
            if meta.key == key:
                return meta.account_id
        return None

    def mark_key_exhausted(self, provider: str, key_val: str, error_type: str = "quota") -> bool:
        """
        Mark a specific key as exhausted or place it in cooldown.
        error_type: "quota" (permanent), "rate_limit" (60s cooldown)
        
        Returns:
            True  — at least one key is still healthy; retry.
            False — all keys exhausted; switch providers.
        """
        keys = self._keys.get(provider)
        if not keys:
            return False

        with self._locks[provider]:
            for meta in keys:
                if meta.key == key_val:
                    meta.failure_count += 1
                    if error_type == "rate_limit":
                        meta.cooldown_until = time.time() + 60.0
                        logger.warning(
                            "key_manager: %s key placed in 60s cooldown (429 Rate Limit)", 
                            provider
                        )
                    else:
                        meta.exhausted = True
                        logger.warning(
                            "key_manager: %s key permanently exhausted (%s)", 
                            provider, error_type
                        )
                    break

            # Check if any keys are still healthy
            return any(m.is_healthy() for m in keys)

    def all_keys_exhausted(self, provider: str) -> bool:
        """Return True if every configured key for this provider is unavailable."""
        keys = self._keys.get(provider)
        if not keys:
            return True

        with self._locks[provider]:
            return not any(m.is_healthy() for m in keys)

    def reset_provider_keys(self, provider: str) -> None:
        """Reset exhaustion/cooldown state for a provider."""
        keys = self._keys.get(provider)
        if not keys:
            return
        with self._locks[provider]:
            for meta in keys:
                meta.exhausted = False
                meta.cooldown_until = 0.0
                meta.failure_count = 0
            self._current_index[provider] = 0
        logger.info("key_manager: reset all keys for provider '%s'", provider)

    def get_key_count(self, provider: str) -> int:
        return len(self._keys.get(provider, []))

    def get_available_providers(self) -> list[str]:
        return [p for p, keys in self._keys.items() if keys]
