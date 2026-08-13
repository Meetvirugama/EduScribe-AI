"""
provider_stats.py — Dynamic Model Scoring and Statistics

Tracks success rate and latency of providers over time to allow
dynamic sorting of the fallback chain (Phase 3 of Resilience Architecture).
Note: Cost tracking is omitted as this system exclusively uses free API tiers.
"""
import collections
import time
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class ProviderStats:
    def __init__(self, window_size: int = 100):
        # Store recent latency and success (1 or 0) per provider/model
        # Key: (provider, model)
        self.window_size = window_size
        self.history: Dict[Tuple[str, str], collections.deque] = {}

    def record_call(self, provider: str, model: str,
                    success: bool, latency: float):
        key = (provider, model)
        if key not in self.history:
            self.history[key] = collections.deque(maxlen=self.window_size)

        self.history[key].append({
            "success": 1 if success else 0,
            "latency": latency,
            "timestamp": time.time()
        })

    def get_stats(self, provider: str, model: str) -> dict:
        key = (provider, model)
        if key not in self.history or len(self.history[key]) == 0:
            return {"success_rate": 1.0, "avg_latency": 0.0, "samples": 0}

        history = self.history[key]
        success_rate = sum(x["success"] for x in history) / len(history)
        avg_latency = sum(x["latency"] for x in history) / len(history)

        return {
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "samples": len(history)
        }

    def calculate_score(self, provider: str, model: str) -> float:
        """
        Dynamic 0–100 score for intra-tier fallback ordering.
        Higher is better. Used by FallbackManager to sort providers
        within each tier by observed reliability and speed.
        70% weight on success rate, 30% on latency.
        """
        stats = self.get_stats(provider, model)
        if stats["samples"] == 0:
            return 50.0  # Neutral score for untested models

        success_score = stats["success_rate"] * 100
        # Normalize latency: 1s = 90pts, 10s = 0pts
        latency_score = max(0.0, 100.0 - (stats["avg_latency"] * 10))
        return round((0.7 * success_score) + (0.3 * latency_score), 2)
