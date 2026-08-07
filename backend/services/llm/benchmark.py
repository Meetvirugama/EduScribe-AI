"""
services/llm/benchmark.py — Model Benchmarking Utility

Allows empirical evaluation of models by running identical prompts
against multiple models concurrently and capturing latency, output size,
and success status.

Issue Resolved: #15 (Need benchmarking suite for A/B trials)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from services.llm.llm_manager import LLMManager
from services.llm.model_selector import TaskType, ModelConfig

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    model_id: str
    latency_ms: float
    output_tokens: int
    success: bool
    error: str = ""
    response: Any = None


class ModelBenchmark:
    """Runs identical prompts against multiple models concurrently."""

    def __init__(self, llm_manager: LLMManager = None) -> None:
        self.llm_manager = llm_manager or LLMManager()

    async def _run_single(self, model_id: str, task: TaskType, messages: List[Dict[str, str]], config: ModelConfig) -> BenchmarkResult:
        """Run a single generation task and measure latency."""
        start = time.perf_counter()
        
        # We need to temporarily override the model to force evaluation
        original_config = config
        eval_config = ModelConfig(
            primary=model_id,
            secondary=original_config.secondary,
            emergency=original_config.emergency,
            temperature=original_config.temperature,
            max_tokens=original_config.max_tokens,
        )

        try:
            import litellm # type: ignore
            response = await litellm.acompletion(
                model=model_id,
                messages=messages,
                temperature=eval_config.temperature,
                max_tokens=eval_config.max_tokens,
            )
            
            elapsed = (time.perf_counter() - start) * 1000
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if hasattr(response, "usage") and response.usage else len(content) // 4
            
            return BenchmarkResult(
                model_id=model_id,
                latency_ms=elapsed,
                output_tokens=output_tokens,
                success=True,
                response=content,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return BenchmarkResult(
                model_id=model_id,
                latency_ms=elapsed,
                output_tokens=0,
                success=False,
                error=str(e)
            )

    async def run_benchmark(self, models: List[str], task: TaskType, messages: List[Dict[str, str]]) -> List[BenchmarkResult]:
        """Run benchmark concurrently across multiple models."""
        from services.llm.model_selector import get_model_config
        config = get_model_config(task)

        tasks = [
            self._run_single(model_id, task, messages, config)
            for model_id in models
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Benchmark task failed critically: {r}")
            else:
                final_results.append(r)
                
        return final_results
