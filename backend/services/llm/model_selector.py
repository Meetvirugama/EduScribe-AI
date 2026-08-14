"""
model_selector.py — Task-to-Model Routing

Implements the routing table that maps every active EduScribe AI task type to
a primary, secondary, and emergency LiteLLM model ID along with the
correct temperature and max_tokens for that task.

LLD Reference: §18.2 Task-to-Model Routing Table
               §18.4 model_selector.py Reference Implementation
               §18.1 Core Routing Principles

Routing principles (§18.1):
    1. Task complexity determines tier — structural tasks (JSON, formatting)
       route to fast, light models. Deep content generation routes to the
       most capable available model.
    2. Quality first, quota second — the routing table specifies intent.
       Quota-awareness is handled by the LiteLLM Proxy and quota_tracker.py.
    3. Every task has three options — primary, secondary, and emergency —
       giving model_selector.py concrete fallback targets without requiring
       runtime decisions.

Capability Classes:
    1. Complex Reasoning & Long Context  → gemini-2.5-pro primary
    2. Cleaning, Formatting & Fast       → gemini-2.5-flash primary
    3. Code & Math Generation            → cloudflare/kimi-k2.7-code primary
    4. Vision & Multimodal               → gemini-2.5-pro primary
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class TaskType(Enum):
    """All task types actively executed by the EduScribe AI LLM pipeline."""

    # ── Phase 1 – Content Preparation ────────────────────────────────────────
    TRANSCRIPT_CLEANING = "transcript_cleaning"
    ROUTING = "routing"
    METADATA_EXTRACTION = "metadata_extraction"

    # ── Phase 2 – Content Understanding ──────────────────────────────────────
    CONCEPT_EXTRACTION = "concept_extraction"
    KEY_POINTS_EXTRACTION = "key_points_extraction"
    RELATIONSHIP_EXTRACTION = "relationship_extraction"
    EXAMPLE_EXTRACTION = "example_extraction"

    # ── Phase 3 – Knowledge Enrichment ───────────────────────────────────────
    DEFINITION_GENERATION = "definition_generation"
    FORMULA_EXPLANATION = "formula_explanation"
    DETAILED_NOTES = "detailed_notes"

    # Redesigned Phase 3 Tasks
    TOPIC_NOTE_WRITING = "topic_note_writing"
    NOTE_REPAIR = "note_repair"

    # ── Phase 4 – Educational Enhancement ────────────────────────────────────
    INTERVIEW_PERSPECTIVE = "interview_perspective"

    # ── Phase 5 – Assessment Generation ──────────────────────────────────────
    QUIZ_GENERATION = "quiz_generation"
    FLASHCARD_GENERATION = "flashcard_generation"
    MIND_MAP_GENERATION = "mind_map"

    # ── Phase 6 – Note Organization ──────────────────────────────────────────
    REVISION_GENERATION = "revision_generation"

    # ── Phase 7 – Quality Assurance ──────────────────────────────────────────


@dataclass
class ModelConfig:
    """
    Configuration for a single task type.

    Attributes:
        primary:     LiteLLM model ID / proxy alias — first choice.
        secondary:   LiteLLM model ID — used when primary quota is exhausted.
        emergency:   LiteLLM model ID — last resort before the task fails.
        temperature: Sampling temperature. Lower = more deterministic.
        max_tokens:  Maximum completion tokens for this task type.
    """
    primary: str
    secondary: str
    emergency: str
    max_tokens: int
    temperature: Optional[float] = None
    validation_policy: str = "STRICT"  # "STRICT" or "DEGRADE"


# ---------------------------------------------------------------------------
# CAPABILITY CLASS HELPERS
# Model IDs as per tasks_plan.md 7-rank fallback specification.
# ---------------------------------------------------------------------------

# ── Capability: Complex Reasoning & Long Context Analysis ──────────────────
_COMPLEX_PRIMARY = "groq/llama-3.3-70b-versatile"
_COMPLEX_SECONDARY = "cohere/command-a-plus-05-2026"
_COMPLEX_EMERGENCY = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"

# ── Capability: Cleaning, Formatting & Fast Processing ────────────────────
_FAST_PRIMARY = "groq/llama-3.3-70b-versatile"
_FAST_SECONDARY = "groq/llama-3.1-8b-instant"
_FAST_EMERGENCY = "cohere/command-a-03-2025"

# ── Capability: Code & Math Generation ────────────────────────────────────
_CODE_PRIMARY = "cloudflare/@cf/moonshotai/kimi-k2.7-code"
_CODE_SECONDARY = "groq/llama-3.3-70b-versatile"
_CODE_EMERGENCY = "cloudflare/@cf/qwen/qwen2.5-coder-32b-instruct"

# ── Capability: Vision & Multimodal Analysis ──────────────────────────────
_VISION_PRIMARY = "gemini/gemini-2.5-pro"
_VISION_SECONDARY = "gemini/gemini-2.5-flash"
_VISION_EMERGENCY = "cloudflare/@cf/meta/llama-3.2-11b-vision-instruct"


# ---------------------------------------------------------------------------
# ROUTING TABLE
# LLD Reference: §18.2 Task-to-Model Routing Table
#
# Temperature guidance:
#   0.0       — Fully deterministic (JSON extraction, embeddings)
#   0.1-0.2   — Near-deterministic (analysis, detection, classification)
#   0.3-0.4   — Balanced (explanations, notes, quiz)
#   0.5-0.6   — Creative (examples, analogies, intuition)
# ---------------------------------------------------------------------------

ROUTING_TABLE: dict[TaskType, ModelConfig] = {

    # ── Phase 1 – Content Preparation ──────────────────────────────────────

    TaskType.TRANSCRIPT_CLEANING: ModelConfig(
        # Fast Processing — clean, format, structure transcript text
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.ROUTING: ModelConfig(
        # Fast Processing — classification/routing
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=512,
    ),
    TaskType.METADATA_EXTRACTION: ModelConfig(
        # Fast Processing — extract title, subject, speaker, duration
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=512,
    ),

    # ── Phase 2: Content Understanding (Extraction & Classification) ───────
    # These tasks require accurate extraction from the text.

    TaskType.EXAMPLE_EXTRACTION: ModelConfig(
        primary="groq/llama-3.3-70b-versatile",
        secondary="gemini/gemini-2.5-flash",
        emergency="cloudflare/@cf/meta/llama-3.1-8b-instruct",
        temperature=0.2, max_tokens=2000
    ),
    TaskType.CONCEPT_EXTRACTION: ModelConfig(
        # Fast Processing — extract key concepts and terminology
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.KEY_POINTS_EXTRACTION: ModelConfig(
        # Fast Processing — extract key points
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.RELATIONSHIP_EXTRACTION: ModelConfig(
        # Fast Processing — extract semantic relationships
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=8192,
    ),

    # ── Phase 3 – Knowledge Enrichment ─────────────────────────────────────

    TaskType.DEFINITION_GENERATION: ModelConfig(
        # Complex Reasoning — generate precise definitions
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),
    TaskType.FORMULA_EXPLANATION: ModelConfig(
        # Code & Math — explain mathematical formulas
        primary="groq/llama-3.3-70b-versatile",
        secondary="gemini/gemini-2.5-flash",
        emergency="cloudflare/meta/llama-3.1-8b-instruct",
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.DETAILED_NOTES: ModelConfig(
        # Complex Reasoning — generate comprehensive notes with citations
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=16384,
    ),
    TaskType.TOPIC_NOTE_WRITING: ModelConfig(
        # Complex Reasoning — core educational note generation
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=16384,
    ),
    TaskType.NOTE_REPAIR: ModelConfig(
        # Complex Reasoning — targeted targeted repair
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=6144,
    ),

    # ── Phase 4 – Educational Enhancement ──────────────────────────────────

    TaskType.INTERVIEW_PERSPECTIVE: ModelConfig(
        # Complex Reasoning — generate interview Q&A perspective
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=4096,
    ),

    # ── Phase 5 – Assessment Generation ────────────────────────────────────

    TaskType.QUIZ_GENERATION: ModelConfig(
        # Complex Reasoning — generate assessment questions
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=4096,
    ),
    TaskType.FLASHCARD_GENERATION: ModelConfig(
        # Fast Processing — generate spaced repetition flashcards
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),
    TaskType.MIND_MAP_GENERATION: ModelConfig(
        # Complex Reasoning — generate mind map structure
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),

    # ── Phase 6 – Note Organization ────────────────────────────────────────

    TaskType.REVISION_GENERATION: ModelConfig(
        # Complex Reasoning — generate revision sheet
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),

    # ── Phase 7 – Quality Assurance ────────────────────────────────────────

}


def get_model_config(task: TaskType) -> ModelConfig:
    """
    Return the ModelConfig for the given TaskType.

    Usage (from llm_manager.py or any service):
        config = get_model_config(TaskType.TOPIC_DETECTION)

    LLD Reference: §18.4 model_selector.py Reference Implementation
    """
    return ROUTING_TABLE[task]
