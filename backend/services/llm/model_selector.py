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
    LECTURE_ANALYSIS = "lecture_analysis"
    TRANSCRIPT_CLEANING = "transcript_cleaning"
    METADATA_EXTRACTION = "metadata_extraction"

    # ── Phase 2 – Content Understanding ──────────────────────────────────────
    TOPIC_DETECTION = "topic_detection"
    SUBTOPIC_DETECTION = "subtopic_detection"
    CONCEPT_EXTRACTION = "concept_extraction"
    KEYWORD_EXTRACTION = "keyword_extraction"
    KEY_POINTS_EXTRACTION = "key_points_extraction"
    RELATIONSHIP_EXTRACTION = "relationship_extraction"
    EXAMPLE_EXTRACTION = "example_extraction"
    LEARNING_OBJECTIVE_DETECTION = "learning_objective_detection"
    PREREQUISITE_DETECTION = "prerequisite_detection"
    DEPENDENCY_DETECTION = "dependency_detection"
    KNOWLEDGE_GAP_ANALYSIS = "knowledge_gap_analysis"
    DIFFICULTY_CLASSIFICATION = "difficulty_classification"

    # ── Phase 3 – Knowledge Enrichment ───────────────────────────────────────
    DEFINITION_GENERATION = "definition_generation"
    DETAILED_EXPLANATION_GEN = "detailed_explanation_generation"
    STEP_BY_STEP_EXPLANATION = "step_by_step_explanation"
    FORMULA_EXPLANATION = "formula_explanation"
    REAL_WORLD_APPLICATIONS = "real_world_applications"
    INDUSTRY_USE_CASES = "industry_use_cases"
    DETAILED_NOTES = "detailed_notes"
    CHUNK_NOTES_GENERATION = "chunk_notes_generation"

    # Redesigned Phase 3 Tasks
    LEARNING_PLAN_GENERATION = "learning_plan_generation"
    TOPIC_NOTE_WRITING = "topic_note_writing"
    ACCURACY_CHECK = "accuracy_check"
    PEDAGOGY_CHECK = "pedagogy_check"
    NOTE_REPAIR = "note_repair"

    # ── Phase 4 – Educational Enhancement ────────────────────────────────────
    EXAMPLE_GENERATION = "example_generation"
    INTERVIEW_PERSPECTIVE = "interview_perspective"

    # ── Phase 5 – Assessment Generation ──────────────────────────────────────
    QUIZ_GENERATION = "quiz_generation"
    FLASHCARD_GENERATION = "flashcard_generation"
    MIND_MAP_GENERATION = "mind_map"

    # ── Phase 6 – Note Organization ──────────────────────────────────────────
    REVISION_GENERATION = "revision_generation"

    # ── Phase 7 – Quality Assurance ──────────────────────────────────────────
    FACT_VERIFICATION = "fact_verification"


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
_FAST_PRIMARY = "groq/llama-3.1-8b-instant"
_FAST_SECONDARY = "gemini/gemini-1.5-flash"
_FAST_EMERGENCY = "cloudflare/meta/llama-3.1-8b-instruct"

_COMPLEX_PRIMARY = "openrouter/openai/gpt-4o-mini"
_COMPLEX_SECONDARY = "openrouter/openai/gpt-4o-mini"
_COMPLEX_EMERGENCY = "groq/llama-3.3-70b-versatile"

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

    TaskType.LECTURE_ANALYSIS: ModelConfig(
        # Complex Reasoning — deep structural understanding of lecture
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=8192,
    ),
    TaskType.TRANSCRIPT_CLEANING: ModelConfig(
        # Fast Processing — clean, format, structure transcript text
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
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
    TaskType.TOPIC_DETECTION: ModelConfig(
        primary="gemini-2.5-flash",
        secondary="gemini/gemini-1.5-flash",
        emergency="cloudflare/meta/llama-3.1-8b-instruct",
        temperature=0.2, max_tokens=1500
    ),

    TaskType.EXAMPLE_EXTRACTION: ModelConfig(
        primary="groq/llama-3.3-70b-versatile",
        secondary="gemini-2.5-flash",
        emergency="cloudflare/meta/llama-3.1-8b-instruct",
        temperature=0.2, max_tokens=2000
    ),
    TaskType.SUBTOPIC_DETECTION: ModelConfig(
        # Complex Reasoning — identify sub-topics within a topic
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.CONCEPT_EXTRACTION: ModelConfig(
        # Fast Processing — extract key concepts and terminology
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.KEYWORD_EXTRACTION: ModelConfig(
        # Fast Processing — extract keywords and key phrases
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
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
    TaskType.LEARNING_OBJECTIVE_DETECTION: ModelConfig(
        # Complex Reasoning — identify intended learning outcomes
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.PREREQUISITE_DETECTION: ModelConfig(
        # Complex Reasoning — identify prerequisite knowledge
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.DEPENDENCY_DETECTION: ModelConfig(
        # Complex Reasoning — map topic dependencies
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.KNOWLEDGE_GAP_ANALYSIS: ModelConfig(
        # Complex Reasoning — identify gaps in lecture coverage
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=8192,
    ),
    TaskType.DIFFICULTY_CLASSIFICATION: ModelConfig(
        # Fast Processing — classify content difficulty level
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=512,
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
    TaskType.DETAILED_EXPLANATION_GEN: ModelConfig(
        # Complex Reasoning — generate detailed subtopic explanations
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=8192,
    ),
    TaskType.STEP_BY_STEP_EXPLANATION: ModelConfig(
        # Complex Reasoning — generate step-by-step breakdowns
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),
    TaskType.FORMULA_EXPLANATION: ModelConfig(
        # Code & Math — explain mathematical formulas
        primary="groq/llama-3.3-70b-versatile",
        secondary="gemini/gemini-1.5-flash",
        emergency="cloudflare/meta/llama-3.1-8b-instruct",
        temperature=0.2,
        max_tokens=8192,
    ),
    TaskType.REAL_WORLD_APPLICATIONS: ModelConfig(
        # Complex Reasoning — generate real-world use cases
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=4096,
    ),
    TaskType.INDUSTRY_USE_CASES: ModelConfig(
        # Complex Reasoning — generate industry-specific use cases
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=4096,
    ),
    TaskType.DETAILED_NOTES: ModelConfig(
        # Complex Reasoning — generate comprehensive notes with citations
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=8192,
    ),
    TaskType.CHUNK_NOTES_GENERATION: ModelConfig(
        # Complex Reasoning — generate focused note section for one chunk
        primary="cloudflare/@cf/meta/llama-3.1-8b-instruct",
        secondary="cloudflare/@cf/meta/llama-3.1-8b-instruct",
        emergency="cloudflare/@cf/meta/llama-3.1-8b-instruct",
        temperature=None,
        max_tokens=8192,
    ),
    TaskType.LEARNING_PLAN_GENERATION: ModelConfig(
        # Fast Processing — structural ordering
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.TOPIC_NOTE_WRITING: ModelConfig(
        # Complex Reasoning — core educational note generation
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=8192,
    ),
    TaskType.ACCURACY_CHECK: ModelConfig(
        # Complex Reasoning — factual verification
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.PEDAGOGY_CHECK: ModelConfig(
        # Fast Processing — pedagogical structure evaluation
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
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

    TaskType.EXAMPLE_GENERATION: ModelConfig(
        # Complex Reasoning — generate illustrative examples
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.5,
        max_tokens=4096,
    ),
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

    TaskType.FACT_VERIFICATION: ModelConfig(
        # Complex Reasoning — verify factual accuracy against transcript
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
}


def get_model_config(task: TaskType) -> ModelConfig:
    """
    Return the ModelConfig for the given TaskType.

    Usage (from llm_manager.py or any service):
        config = get_model_config(TaskType.TOPIC_DETECTION)

    LLD Reference: §18.4 model_selector.py Reference Implementation
    """
    return ROUTING_TABLE[task]
