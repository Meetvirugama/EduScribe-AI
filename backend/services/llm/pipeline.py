import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .model_selector import TaskType

logger = logging.getLogger(__name__)

@dataclass
class Capabilities:
    requires_vision: bool = False
    requires_json: bool = False
    requires_long_context: bool = False
    requires_tools: bool = False

@dataclass
class RequestContext:
    task: TaskType
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: Capabilities = field(default_factory=Capabilities)
    
    # Internal routing fields computed by the pipeline
    estimated_tokens: int = 0
    min_context_window: int = 0
    request_id: str = ""

class CapabilityDetector:
    """Analyzes the request payload to determine the required capabilities."""
    
    @staticmethod
    def detect(messages: List[Dict[str, Any]], expected_output_format: str = "text") -> Capabilities:
        cap = Capabilities()
        
        if expected_output_format.lower() == "json":
            cap.requires_json = True
            
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        cap.requires_vision = True
                        break
            if cap.requires_vision:
                break
                
        return cap

class RequestCache:
    """A basic dictionary-based cache. In production, connect this to Redis."""
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        
    def _generate_key(self, context: RequestContext) -> str:
        # Create a deterministic hash of the messages and task
        state = {
            "task": context.task.value,
            "messages": context.messages,
            "temp": context.temperature,
            "tokens": context.max_tokens
        }
        state_str = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()
        
    def get(self, context: RequestContext) -> Optional[Any]:
        key = self._generate_key(context)
        return self._cache.get(key)
        
    def set(self, context: RequestContext, response: Any) -> None:
        key = self._generate_key(context)
        self._cache[key] = response

class MetricsRecorder:
    """Records basic metrics for observability and potential billing."""
    @staticmethod
    def record(context: RequestContext, provider: str, model: str, latency: float, usage: dict) -> None:
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", in_tokens + out_tokens)
        
        logger.info(
            f"LLM_REQUEST_SUCCESS | req_id={context.request_id} | task={context.task.value} | "
            f"provider={provider} | model={model} | latency={latency:.2f}s | "
            f"in_tokens={in_tokens} | out_tokens={out_tokens} | total_tokens={total_tokens}"
        )
