"""
response_parser.py — Normalise and Validate Raw LLM Responses

Converts the raw LiteLLM response object into a consistent internal
dictionary format before it is passed to PydanticAI schema validation.
Every downstream pipeline stage receives a response in this standard form,
regardless of which provider actually generated it.

This module also provides the Pydantic schemas for all pipeline stages,
directly implementing §17.2 of the LLD. PydanticAI uses these schemas
to validate and auto-retry LLM responses.

LLD Reference: §17 PydanticAI
               §17.2 Schema Definitions for All Pipeline Stages
               §17.3 Validation Flow and Auto-Retry
               §16.3 Usage in Application Code
"""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ===========================================================================
# §17.2 — Pydantic Schema Definitions for All Pipeline Stages
#
# These schemas are the contracts that every LLM call in EduScribe AI
# must satisfy. PydanticAI validates each response against the relevant
# schema immediately after LiteLLM returns, before the result reaches
# any business logic.
# ===========================================================================

# Stage 1 — Lecture Analysis (§3.2 Prompt Pipeline, Stage 1)
class LectureAnalysis(BaseModel):
    subject: str
    difficulty: int = Field(ge=1, le=5)   # 1 = beginner, 5 = expert
    prerequisites: list[str]
    teaching_style: str
    primary_objectives: list[str]
    estimated_topics: int = Field(ge=1)


# Stage 2 — Topic Detection (§3.2 Prompt Pipeline, Stage 2)
class Topic(BaseModel):
    title: str
    start_time: str                        # "HH:MM:SS"
    end_time: str
    confidence: float = Field(ge=0.0, le=1.0)

class TopicList(BaseModel):
    topics: list[Topic]


# Stage 3 — Subtopic Detection (§3.2 Prompt Pipeline, Stage 3)
class SubtopicList(BaseModel):
    topic: str
    subtopics: list[str] = Field(min_length=1)


# Stage 4 — Knowledge Gap Analysis (§3.2 Prompt Pipeline, Stage 4)
class KnowledgeGap(BaseModel):
    missing_definitions: list[str]
    missing_prerequisites: list[str]
    implicit_reasoning: list[str]
    potential_misconceptions: list[str]


# Stage 5 — Explanation / Detailed Notes (§3.2 Prompt Pipeline, Stage 5)
# Free-text output — validated for completeness and key field presence.
# NOTE: explanation length is intentionally uncapped (§8, §24.2 Important Notes).
class SubtopicExplanation(BaseModel):
    subtopic: str
    definition: str
    motivation: str
    step_by_step: str
    worked_example: str
    common_mistakes: list[str]
    key_takeaways: list[str]
    frame_references: list[str]           # OCR frame IDs from vision pipeline
    word_count: Optional[int] = None


# Stage 6 — Example Generation (§3.2 Prompt Pipeline, Stage 6)
class ExampleSet(BaseModel):
    subtopic: str
    simple_examples: list[str]
    intermediate_examples: list[str]
    real_world_applications: list[str]
    numerical_examples: Optional[list[str]] = None
    programming_examples: Optional[list[str]] = None
    visual_examples: Optional[list[str]] = None


# Stage 9 — Quiz Generation
class QuizQuestion(BaseModel):
    question: str
    question_type: str                    # "mcq", "true_false", "fill_blank", "hots"
    options: Optional[list[str]] = None   # MCQ choices
    correct_answer: str
    explanation: str
    difficulty: int = Field(ge=1, le=5)

class QuizSet(BaseModel):
    topic: str
    subtopic: str
    questions: list[QuizQuestion]


# Flashcard schema
class Flashcard(BaseModel):
    front: str
    back: str
    tags: Optional[list[str]] = None

class FlashcardSet(BaseModel):
    topic: str
    flashcards: list[Flashcard]


# Mind Map schema (text-based: Mermaid / Markdown tree)
class MindMap(BaseModel):
    topic: str
    format: str                            # "mermaid", "markdown_tree", "nested_bullets"
    content: str


# ===========================================================================
# Response Parser
# ===========================================================================

class ResponseParser:
    """
    Normalises raw LiteLLM API responses into a consistent internal
    dictionary format before schema validation.

    Every provider returns a slightly different object structure. This class
    extracts the text content, usage statistics, and model metadata from
    whatever LiteLLM returns, producing a stable dict that downstream
    code (PydanticAI validators, llm_manager.py) can always rely on.

    LLD Reference: §16.3 Usage in Application Code,
                   §15.3 Folder Structure — "Normalise + validate raw LLM responses"
    """

    @staticmethod
    def parse(raw_response: Any, provider: str = "unknown") -> dict[str, Any]:
        """
        Parse a raw LiteLLM response object into a normalised dict.

        Args:
            raw_response: The object returned by litellm.acompletion().
            provider:     Provider name for logging.

        Returns:
            {
                "content": str,             # model's text response
                "model": str,               # model ID that was used
                "provider": str,            # provider name
                "usage": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int,
                },
                "finish_reason": str,       # "stop", "length", etc.
                "raw": Any,                 # original response (for debugging)
            }

        Raises:
            ResponseParseError: If the response is None or has an unexpected shape.
        """
        if raw_response is None:
            raise ResponseParseError("LiteLLM returned None — provider may have errored.")

        try:
            # LiteLLM returns an openai.types.chat.ChatCompletion-compatible object
            choice = raw_response.choices[0]
            content: str = choice.message.content or ""

            usage_obj = getattr(raw_response, "usage", None)
            usage = {
                "prompt_tokens":     getattr(usage_obj, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage_obj, "completion_tokens", 0) or 0,
                "total_tokens":      getattr(usage_obj, "total_tokens", 0) or 0,
            }

            return {
                "content":       content,
                "model":         getattr(raw_response, "model", "unknown"),
                "provider":      provider,
                "usage":         usage,
                "finish_reason": getattr(choice, "finish_reason", "unknown"),
                "raw":           raw_response,
            }

        except (AttributeError, IndexError, TypeError) as exc:
            logger.error(
                "response_parser: failed to parse response from '%s': %s\n"
                "Raw response: %r",
                provider,
                exc,
                raw_response,
            )
            raise ResponseParseError(
                f"Could not parse LiteLLM response from '{provider}': {exc}"
            ) from exc

    @staticmethod
    def extract_json(content: str) -> Any:
        """
        Extract and parse JSON from a model response string.

        Handles the common case where the model wraps JSON in a
        markdown code fence (```json ... ```).

        Args:
            content: Raw text content from the LLM response.

        Returns:
            Parsed Python object (dict, list, etc.).

        Raises:
            json.JSONDecodeError: If no valid JSON can be extracted.
        """
        # Strip markdown fences if present
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            # Remove first line (```json or ```) and last line (```)
            inner_lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            stripped = "\n".join(inner_lines).strip()

        return json.loads(stripped)

    @staticmethod
    def is_truncated(parsed: dict[str, Any]) -> bool:
        """
        Return True if the model stopped due to hitting max_tokens
        (finish_reason == "length"), indicating a truncated response.
        Truncated JSON should not be passed to PydanticAI validation.

        LLD Reference: §17.1 — "Truncated JSON when the model hits max_tokens"
        """
        return parsed.get("finish_reason") == "length"


class ResponseParseError(Exception):
    """
    Raised when raw_response cannot be normalised into the standard dict.
    Treated as a transient error by the LLM Manager (triggers retry).
    """
