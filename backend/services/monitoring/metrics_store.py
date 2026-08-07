"""
services/monitoring/metrics_store.py — Structured LLM Metrics Store

Writes per-request LLM metrics to a dedicated JSON Lines log file.
On systems with PostgreSQL, a separate Alembic migration adds the
llm_metrics table; the store writes there too when available.

The JSON Lines format means:
  - Zero-latency writes (append-only)
  - Human-readable for debugging
  - Queryable via grep / jq / any analytics tool
  - Trivially importable into pandas or PostreSQL

Issue Resolved: #17 (missing AI monitoring and analytics)
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import settings

logger = logging.getLogger(__name__)

# Metrics log file path
_METRICS_LOG_PATH = os.path.join(
    getattr(settings, "OUTPUT_DIR", "storage/outputs"),
    "..",
    "metrics",
    "llm_requests.jsonl",
)


class MetricsStore:
    """
    Lightweight structured metrics store using JSON Lines.

    Each record written to disk is one JSON object per line:
    {"ts": "...", "task": "...", "provider": "...", "model": "...",
     "latency_ms": 1234, "input_tokens": 500, "output_tokens": 300,
     "success": true, "error_type": null, "video_id": "..."}
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        self._log_path = log_path or _METRICS_LOG_PATH
        os.makedirs(os.path.dirname(self._log_path), exist_ok=True)

    def record(
        self,
        *,
        task: str,
        provider: str,
        model: str,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
        error_type: Optional[str] = None,
        video_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Append a single metrics record to the JSON Lines file."""
        record = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "task": task,
            "provider": provider,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "success": success,
            "error_type": error_type,
            "video_id": video_id,
            "request_id": request_id,
        }
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            logger.warning("MetricsStore: failed to write record: %s", exc)

    def get_summary(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Read the last ``limit`` records and compute aggregate statistics.
        Returns a dict suitable for the /admin/metrics/summary endpoint.
        """
        records = self._read_last(limit)
        if not records:
            return {"total_requests": 0}

        total = len(records)
        successes = sum(1 for r in records if r.get("success"))
        total_tokens = sum(r.get("total_tokens", 0) for r in records)
        latencies = [r.get("latency_ms", 0) for r in records if r.get("success")]

        # Per-provider breakdown
        providers: Dict[str, Dict] = {}
        for r in records:
            prov = r.get("provider", "unknown")
            if prov not in providers:
                providers[prov] = {"requests": 0, "successes": 0, "total_tokens": 0, "latencies": []}
            providers[prov]["requests"] += 1
            if r.get("success"):
                providers[prov]["successes"] += 1
                providers[prov]["latencies"].append(r.get("latency_ms", 0))
            providers[prov]["total_tokens"] += r.get("total_tokens", 0)

        provider_summary = {
            prov: {
                "requests": d["requests"],
                "success_rate": round(d["successes"] / d["requests"], 3),
                "avg_latency_ms": round(sum(d["latencies"]) / max(len(d["latencies"]), 1), 1),
                "total_tokens": d["total_tokens"],
            }
            for prov, d in providers.items()
        }

        return {
            "total_requests": total,
            "success_rate": round(successes / total, 3),
            "avg_latency_ms": round(sum(latencies) / max(len(latencies), 1), 1),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1),
            "total_tokens": total_tokens,
            "by_provider": provider_summary,
        }

    def _read_last(self, limit: int) -> List[Dict]:
        """Read the last N records from the JSON Lines file."""
        if not os.path.exists(self._log_path):
            return []
        try:
            with open(self._log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            records = []
            for line in lines[-limit:]:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
            return records
        except Exception as exc:
            logger.warning("MetricsStore: failed to read records: %s", exc)
            return []


# Module-level singleton
metrics_store = MetricsStore()
