import json
import logging
import re
from typing import Any
from .exceptions import JSONExtractionError

logger = logging.getLogger(__name__)

class JSONExtractor:
    """
    Advanced JSON extractor with repair heuristics.
    """
    @staticmethod
    def extract_and_repair(content: str) -> dict[str, Any]:
        # 1. Strip markdown code fences
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            inner_lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            stripped = "\n".join(inner_lines).strip()

        # 2. Try standard parse
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON standard parse failed: {e}. Attempting repair.")
            pass

        # 3. Repair heuristics
        repaired = stripped
        # Remove trailing commas
        repaired = re.sub(r",\s*([\]}])", r"\1", repaired)
        
        # 4. Try repaired parse
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to repair JSON: {e}\nRaw content: {content}")
            raise JSONExtractionError(f"Could not extract or repair JSON: {e}") from e
