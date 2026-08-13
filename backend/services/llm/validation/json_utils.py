import json
import logging
from typing import Any
from .exceptions import JSONExtractionError

logger = logging.getLogger(__name__)


class JSONExtractor:
    """
    Advanced JSON extractor with robust, safe heuristics.
    """

    @staticmethod
    def _remove_trailing_commas(json_str: str) -> str:
        """Safely removes trailing commas before closing braces/brackets, ignoring strings."""
        in_string = False
        escape = False
        result = []

        for i, char in enumerate(json_str):
            if escape:
                escape = False
                result.append(char)
                continue

            if char == '\\':
                escape = True
                result.append(char)
                continue

            if char == '"':
                in_string = not in_string
                result.append(char)
                continue

            if not in_string and char == ',':
                # Check if next non-whitespace char is } or ]
                j = i + 1
                while j < len(json_str) and json_str[j].isspace():
                    j += 1
                if j < len(json_str) and json_str[j] in ']}':
                    continue  # Skip the comma safely

            result.append(char)

        return "".join(result)

    @staticmethod
    def extract_and_repair(content: str) -> dict[str, Any]:
        if not content or not content.strip():
            raise JSONExtractionError("Cannot extract JSON from empty content")

        stripped = content.strip()

        # 1. Locate JSON object bounds (ignore surrounding prose)
        start_idx = stripped.find('{')
        end_idx = stripped.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = stripped[start_idx:end_idx + 1]
        else:
            candidate = stripped

        # 2. Try standard parse
        try:
            result = json.loads(candidate)
            if not isinstance(result, dict):
                raise JSONExtractionError(
                    f"Expected JSON object, got {type(result).__name__}")
            return result
        except json.JSONDecodeError as e:
            logger.debug(
                f"JSON standard parse failed: {e}. Attempting safe repairs.")

        # 3. Safe Repair heuristics
        repaired = JSONExtractor._remove_trailing_commas(candidate)

        # 4. Try repaired parse
        try:
            result = json.loads(repaired)
            if not isinstance(result, dict):
                raise JSONExtractionError(
                    f"Expected JSON object, got {type(result).__name__}")
            return result
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to repair JSON: {e}\nRaw content preview: {content[:200]}...")
            raise JSONExtractionError(
                f"Could not extract or repair JSON: {e}") from e
