"""
model_selector.py — Task-to-Model Routing

Implements the routing table that maps every EduScribe AI task type to
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

Capability Classes (from tasks_plan.md):
    1. Complex Reasoning & Long Context  → gemini-2.5-pro primary
    2. Cleaning, Formatting & Fast       → gemini-2.5-flash primary
    3. Code & Math Generation            → cloudflare/kimi-k2.7-code primary
    4. Vision & Multimodal               → gemini-2.5-pro primary
    5. Embeddings & Vector Search        → gemini-embedding-2 primary
"""

import hashlib
import random
from enum import Enum
from dataclasses import dataclass


class TaskType(Enum):
    """All task categories executed by the EduScribe AI LLM pipeline.

    Phases 1-10 as defined in tasks_plan.md (T01–T100).
    """

    # ── Phase 1 – Content Preparation (T01–T10) ──────────────────────────────
    LECTURE_ANALYSIS            = "lecture_analysis"           # T01
    TRANSCRIPT_CLEANING         = "transcript_cleaning"        # T02
    OCR_TEXT_CLEANING           = "ocr_text_cleaning"          # T03
    TRANSCRIPT_OCR_FUSION       = "transcript_ocr_fusion"      # T04
    TIMESTAMP_ALIGNMENT         = "timestamp_alignment"        # T05
    FRAME_ASSOCIATION           = "frame_association"          # T06
    METADATA_EXTRACTION         = "metadata_extraction"        # T07
    LANGUAGE_DETECTION          = "language_detection"         # T08
    CONTENT_NORMALIZATION       = "content_normalization"      # T09
    SEMANTIC_CHUNKING           = "semantic_chunking"          # T10

    # ── Phase 2 – Content Understanding (T11–T20) ────────────────────────────
    TOPIC_DETECTION             = "topic_detection"            # T11
    SUBTOPIC_DETECTION          = "subtopic_detection"         # T12
    CONCEPT_EXTRACTION          = "concept_extraction"         # T13
    KEYWORD_EXTRACTION          = "keyword_extraction"         # T14
    LEARNING_OBJECTIVE_DETECTION= "learning_objective_detection"# T15
    PREREQUISITE_DETECTION      = "prerequisite_detection"     # T16
    DEPENDENCY_DETECTION        = "dependency_detection"       # T17
    KNOWLEDGE_TREE_GENERATION   = "knowledge_tree_generation"  # T18
    KNOWLEDGE_GAP               = "knowledge_gap"              # T19
    DIFFICULTY_CLASSIFICATION   = "difficulty_classification"  # T20

    # ── Phase 3 – Knowledge Enrichment (T21–T35) ─────────────────────────────
    DEFINITION_GENERATION       = "definition_generation"      # T21
    DETAILED_EXPLANATION_GEN    = "detailed_explanation_generation" # T22
    INTUITION_GENERATION        = "intuition_generation"       # T23
    STEP_BY_STEP_EXPLANATION    = "step_by_step_explanation"   # T24
    ALGORITHM_EXPLANATION       = "algorithm_explanation"      # T25
    FORMULA_EXPLANATION         = "formula_explanation"        # T26
    MATHEMATICAL_DERIVATION     = "mathematical_derivation"    # T27
    CODE_EXPLANATION            = "code_explanation"           # T28
    PSEUDOCODE_GENERATION       = "pseudocode_generation"      # T29
    ANALOGY_GENERATION          = "analogy_generation"         # T30
    REAL_WORLD_APPLICATIONS     = "real_world_applications"    # T31
    INDUSTRY_USE_CASES          = "industry_use_cases"         # T32
    HISTORICAL_CONTEXT          = "historical_context"         # T33
    CROSS_TOPIC_REFERENCES      = "cross_topic_references"     # T34
    DETAILED_NOTES              = "detailed_notes"             # T35 (was T-legacy)

    # ── Phase 4 – Educational Enhancement (T36–T45) ──────────────────────────
    EXAMPLE_GENERATION          = "example_generation"         # T36
    NUMERICAL_EXAMPLE_GENERATION= "numerical_example_generation" # T37
    PROGRAMMING_EXAMPLE_GEN     = "programming_example_generation" # T38
    VISUAL_EXAMPLE_EXPLANATION  = "visual_example_explanation" # T39
    COMMON_MISTAKES_DETECTION   = "common_mistakes_detection"  # T40
    MISCONCEPTION_DETECTION     = "misconception_detection"    # T41
    BEST_PRACTICES_GENERATION   = "best_practices_generation"  # T42
    EDGE_CASE_DETECTION         = "edge_case_detection"        # T43
    INTERVIEW_PERSPECTIVE       = "interview_perspective"      # T44
    PRACTICAL_TIPS              = "practical_tips"             # T45

    # ── Phase 5 – Assessment Generation (T46–T53) ────────────────────────────
    QUIZ_GENERATION             = "quiz_generation"            # T46
    FLASHCARD_GENERATION        = "flashcard_generation"       # T47
    MIND_MAP_GENERATION         = "mind_map"                   # T48
    PROGRAMMING_EXPLAIN         = "programming_explanation"    # T49
    MATHEMATICS                 = "mathematics"                # T50
    KNOWLEDGE_GAP_ANALYSIS      = "knowledge_gap_analysis"     # T51
    IMPORTANT_NOTES_ID          = "important_notes_identification" # T52
    LEARNING_PATH_RECOMMENDATION= "learning_path_recommendation" # T53

    # ── Phase 6 – Note Organization (T54–T65) ────────────────────────────────
    NOTE_STRUCTURING            = "note_structuring"           # T54
    TABLE_OF_CONTENTS_GEN       = "table_of_contents_generation" # T55
    SECTION_SUMMARIZATION       = "section_summarization"      # T56
    BULLET_POINT_EXTRACTION     = "bullet_point_extraction"    # T57
    HIGHLIGHT_EXTRACTION        = "highlight_extraction"       # T58
    REVISION_GENERATION         = "revision_generation"        # T59
    TAG_GENERATION              = "tag_generation"             # T59
    VISUAL_DIAGRAM_DESCRIPTION  = "visual_diagram_description" # T60
    OCR_CORRECTION              = "ocr_correction"             # T61 (legacy alias)
    MARKDOWN_FORMAT             = "markdown_format"            # T62
    REFERENCE_LINKING           = "reference_linking"          # T63
    HTML_GENERATION             = "html_generation"            # T64
    PDF_GENERATION              = "pdf_generation"             # T65

    # ── Phase 7 – Quality Assurance (T66–T75) ────────────────────────────────
    FACT_VERIFICATION           = "fact_verification"          # T66
    TRANSCRIPT_CONSISTENCY_CHECK= "transcript_consistency_check" # T67
    OCR_CONSISTENCY_CHECK       = "ocr_consistency_check"      # T68
    DUPLICATE_DETECTION         = "duplicate_detection"        # T69
    COMPLETENESS_CHECK          = "completeness_check"         # T70
    ACCURACY_SCORING            = "accuracy_scoring"           # T71
    READABILITY_SCORING         = "readability_scoring"        # T72
    BIAS_DETECTION              = "bias_detection"             # T73
    CITATION_VERIFICATION       = "citation_verification"      # T74
    GRAMMAR_CHECK               = "grammar_check"              # T75

    # ── Phase 8 – Search & Retrieval (T76–T82) ───────────────────────────────
    DOCUMENT_EMBEDDING          = "document_embedding"         # T76
    EMBEDDING_OPTIMIZATION      = "embedding_optimization"     # T77
    VECTOR_INDEX_CREATION       = "vector_index_creation"      # T78
    SEMANTIC_SEARCH_INDEXING    = "semantic_search_indexing"   # T79
    RAG_ANSWERING               = "rag_answering"              # T80
    RAG_DOCUMENT_PREPARATION    = "rag_document_preparation"   # T81
    KNOWLEDGE_GRAPH_GENERATION  = "knowledge_graph_generation" # T82
    METADATA_INDEXING           = "metadata_indexing"          # T83

    # ── Phase 9 – Future Features (T83–T90) ──────────────────────────────────
    PERSONALIZED_LEARNING_META  = "personalized_learning_metadata" # T84
    STUDY_PROGRESS_ANALYTICS    = "study_progress_analytics"   # T85
    CONCEPT_RELATIONSHIP_GRAPH  = "concept_relationship_graph" # T86
    LEARNING_RECOMMENDATION_ENGINE = "learning_recommendation_engine" # T87
    AI_TUTOR_KNOWLEDGE_BASE     = "ai_tutor_knowledge_base"    # T88

    # ── Phase 10 – System Management (T89–T100) ──────────────────────────────
    PROMPT_SELECTION            = "prompt_selection"           # T89
    PROMPT_VERSION_MANAGEMENT   = "prompt_version_management"  # T90
    JSON_EXTRACTION             = "json_extraction"            # utility
    CODE_GENERATION             = "code_generation"            # utility


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
    primary:     str
    secondary:   str
    emergency:   str
    temperature: float
    max_tokens:  int


@dataclass
class ModelExperiment:
    """
    A/B test definition for evaluating alternative models in production.
    """
    model_a: str           # The control model
    model_b: str           # The treatment model
    traffic_split: float   # 0.0 to 1.0 (e.g. 0.2 means 20% traffic goes to model_b)

# Active experiments mapping TaskType to ModelExperiment
_EXPERIMENT_REGISTRY = {}

def register_experiment(task: TaskType, experiment: ModelExperiment):
    """Register an A/B test for a specific task."""
    _EXPERIMENT_REGISTRY[task] = experiment

def unregister_experiment(task: TaskType):
    """Remove an A/B test."""
    if task in _EXPERIMENT_REGISTRY:
        del _EXPERIMENT_REGISTRY[task]


# ---------------------------------------------------------------------------
# CAPABILITY CLASS HELPERS
# Model IDs as per tasks_plan.md 7-rank fallback specification.
# ---------------------------------------------------------------------------

# ── Capability: Complex Reasoning & Long Context Analysis ──────────────────
# Rank 1: Gemini 2.5 Pro, Rank 2: Cohere command-a-plus, Rank 3+: OpenRouter/Cloudflare
_COMPLEX_PRIMARY   = "gemini/gemini-2.5-pro"
_COMPLEX_SECONDARY = "cohere/command-a-plus-05-2026"
_COMPLEX_EMERGENCY = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"

# ── Capability: Cleaning, Formatting & Fast Processing ────────────────────
# Rank 1: Gemini 2.5 Flash, Rank 2: Groq Llama 3.3 70B, Rank 3: Cohere command-a
_FAST_PRIMARY   = "gemini/gemini-2.5-flash"
_FAST_SECONDARY = "groq/llama-3.3-70b-versatile"
_FAST_EMERGENCY = "cohere/command-a-03-2025"

# ── Capability: Code & Math Generation ────────────────────────────────────
# Rank 1: Cloudflare Kimi K2.7 Code, Rank 2: Gemini 2.5 Pro, Rank 3: Cloudflare Qwen Coder
_CODE_PRIMARY   = "cloudflare/@cf/moonshotai/kimi-k2.7-code"
_CODE_SECONDARY = "gemini/gemini-2.5-pro"
_CODE_EMERGENCY = "cloudflare/@cf/qwen/qwen2.5-coder-32b-instruct"

# ── Capability: Vision & Multimodal Analysis ──────────────────────────────
# Rank 1: Gemini 2.5 Pro, Rank 2: Gemini 2.5 Flash, Rank 3: Cloudflare Llama Vision
_VISION_PRIMARY   = "gemini/gemini-2.5-pro"
_VISION_SECONDARY = "gemini/gemini-2.5-flash"
_VISION_EMERGENCY = "cloudflare/@cf/meta/llama-3.2-11b-vision-instruct"

# ── Capability: Embeddings & Vector Search ────────────────────────────────
# Rank 1: Gemini Embedding, Rank 2: Jina Embeddings, Rank 3: Cloudflare BGE
_EMBED_PRIMARY   = "gemini/text-embedding-004"
_EMBED_SECONDARY = "jina/jina-embeddings-v3"
_EMBED_EMERGENCY = "cloudflare/@cf/baai/bge-m3"


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
        max_tokens=2048,
    ),
    TaskType.TRANSCRIPT_CLEANING: ModelConfig(
        # Fast Processing — clean, format, structure transcript text
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.OCR_TEXT_CLEANING: ModelConfig(
        # Vision — understand and clean OCR-extracted text from frames
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.TRANSCRIPT_OCR_FUSION: ModelConfig(
        # Vision — fuse transcript with OCR data using spatial understanding
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.TIMESTAMP_ALIGNMENT: ModelConfig(
        # Fast Processing — align timestamps between transcript and frames
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=2048,
    ),
    TaskType.FRAME_ASSOCIATION: ModelConfig(
        # Vision — associate transcript segments with visual frames
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.METADATA_EXTRACTION: ModelConfig(
        # Fast Processing — extract title, subject, duration, metadata
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=1024,
    ),
    TaskType.LANGUAGE_DETECTION: ModelConfig(
        # Fast Processing — detect language of transcript
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),
    TaskType.CONTENT_NORMALIZATION: ModelConfig(
        # Fast Processing — normalize text, fix encoding, clean noise
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.SEMANTIC_CHUNKING: ModelConfig(
        # Fast Processing — split content into semantic chunks
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=2048,
    ),

    # ── Phase 2 – Content Understanding ────────────────────────────────────

    TaskType.TOPIC_DETECTION: ModelConfig(
        # Complex Reasoning — detect high-level topics in lecture
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.SUBTOPIC_DETECTION: ModelConfig(
        # Complex Reasoning — identify subtopics under each topic
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.CONCEPT_EXTRACTION: ModelConfig(
        # Complex Reasoning — extract key academic/technical concepts
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.KEYWORD_EXTRACTION: ModelConfig(
        # Fast Processing — extract important keywords and phrases
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=512,
    ),
    TaskType.LEARNING_OBJECTIVE_DETECTION: ModelConfig(
        # Fast Processing — identify what the lecture teaches
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.PREREQUISITE_DETECTION: ModelConfig(
        # Complex Reasoning — detect required prior knowledge
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.DEPENDENCY_DETECTION: ModelConfig(
        # Complex Reasoning — detect concept dependencies within content
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.KNOWLEDGE_TREE_GENERATION: ModelConfig(
        # Complex Reasoning — build hierarchical knowledge structure
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.KNOWLEDGE_GAP: ModelConfig(
        # Complex Reasoning — identify gaps in content coverage
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.DIFFICULTY_CLASSIFICATION: ModelConfig(
        # Fast Processing — classify difficulty level (1-5)
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),

    # ── Phase 3 – Knowledge Enrichment ─────────────────────────────────────

    TaskType.DEFINITION_GENERATION: ModelConfig(
        # Fast Processing — generate clear definitions for terms
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.DETAILED_EXPLANATION_GEN: ModelConfig(
        # Complex Reasoning — generate in-depth explanations
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=8192,
    ),
    TaskType.INTUITION_GENERATION: ModelConfig(
        # Complex Reasoning — build intuitive understanding of concepts
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=4096,
    ),
    TaskType.STEP_BY_STEP_EXPLANATION: ModelConfig(
        # Complex Reasoning — break down processes into clear steps
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),
    TaskType.ALGORITHM_EXPLANATION: ModelConfig(
        # Code & Math — explain algorithms with pseudocode and complexity
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.2,
        max_tokens=4096,
    ),
    TaskType.FORMULA_EXPLANATION: ModelConfig(
        # Code & Math — break down mathematical formulas
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.MATHEMATICAL_DERIVATION: ModelConfig(
        # Code & Math — step-by-step mathematical derivations
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.CODE_EXPLANATION: ModelConfig(
        # Code & Math — explain code logic, patterns, and design
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.2,
        max_tokens=4096,
    ),
    TaskType.PSEUDOCODE_GENERATION: ModelConfig(
        # Code & Math — generate pseudocode from descriptions
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.ANALOGY_GENERATION: ModelConfig(
        # Complex Reasoning — generate analogies for difficult concepts
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.5,
        max_tokens=2048,
    ),
    TaskType.REAL_WORLD_APPLICATIONS: ModelConfig(
        # Fast Processing — list real-world use cases for concepts
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.INDUSTRY_USE_CASES: ModelConfig(
        # Fast Processing — industry-specific application examples
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.HISTORICAL_CONTEXT: ModelConfig(
        # Fast Processing — historical background of concepts
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.CROSS_TOPIC_REFERENCES: ModelConfig(
        # Complex Reasoning — identify links between topics
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.DETAILED_NOTES: ModelConfig(
        # Complex Reasoning — generate comprehensive structured notes
        # No upper limit on explanation length (§8 Token-Agnostic Quality)
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=8192,
    ),

    # ── Phase 4 – Educational Enhancement ──────────────────────────────────

    TaskType.EXAMPLE_GENERATION: ModelConfig(
        # Fast Processing — generate illustrative examples
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.5,
        max_tokens=4096,
    ),
    TaskType.NUMERICAL_EXAMPLE_GENERATION: ModelConfig(
        # Complex Reasoning — generate numerical / mathematical examples
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.PROGRAMMING_EXAMPLE_GEN: ModelConfig(
        # Code & Math — generate runnable code examples
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),
    TaskType.VISUAL_EXAMPLE_EXPLANATION: ModelConfig(
        # Vision — explain visual examples from keyframes
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.COMMON_MISTAKES_DETECTION: ModelConfig(
        # Complex Reasoning — identify common learner mistakes
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.MISCONCEPTION_DETECTION: ModelConfig(
        # Complex Reasoning — identify conceptual misconceptions
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.BEST_PRACTICES_GENERATION: ModelConfig(
        # Fast Processing — generate domain best practices
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.EDGE_CASE_DETECTION: ModelConfig(
        # Complex Reasoning — identify edge cases and corner cases
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.INTERVIEW_PERSPECTIVE: ModelConfig(
        # Fast Processing — frame content for interview/exam preparation
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.PRACTICAL_TIPS: ModelConfig(
        # Fast Processing — actionable practical tips for learners
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),

    # ── Phase 5 – Assessment Generation ────────────────────────────────────

    TaskType.QUIZ_GENERATION: ModelConfig(
        # Complex Reasoning — generate high-quality assessment questions
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.4,
        max_tokens=4096,
    ),
    TaskType.FLASHCARD_GENERATION: ModelConfig(
        # Fast Processing — create study flashcards
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.REVISION_GENERATION: ModelConfig(
        # Complex Reasoning — generate high-quality concise revision material
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.MIND_MAP_GENERATION: ModelConfig(
        # Complex Reasoning — generate Mermaid mind map structure
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.PROGRAMMING_EXPLAIN: ModelConfig(
        # Code & Math — explain programming concepts and patterns
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.3,
        max_tokens=8192,
    ),
    TaskType.MATHEMATICS: ModelConfig(
        # Code & Math — solve and explain mathematical problems
        # Kimi K2.7 Code excels at math reasoning and LaTeX
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency="groq/llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=8192,
    ),
    TaskType.KNOWLEDGE_GAP_ANALYSIS: ModelConfig(
        # Complex Reasoning — deep analysis of knowledge gaps
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.IMPORTANT_NOTES_ID: ModelConfig(
        # Fast Processing — identify the most important notes/highlights
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.LEARNING_PATH_RECOMMENDATION: ModelConfig(
        # Complex Reasoning — recommend personalized learning paths
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),

    # ── Phase 6 – Note Organization ────────────────────────────────────────

    TaskType.NOTE_STRUCTURING: ModelConfig(
        # Fast Processing — organize notes into clear structure
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.TABLE_OF_CONTENTS_GEN: ModelConfig(
        # Fast Processing — generate table of contents
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=1024,
    ),
    TaskType.SECTION_SUMMARIZATION: ModelConfig(
        # Fast Processing — summarize individual note sections
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.BULLET_POINT_EXTRACTION: ModelConfig(
        # Fast Processing — extract key bullet points
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.HIGHLIGHT_EXTRACTION: ModelConfig(
        # Fast Processing — extract must-know highlights
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.TAG_GENERATION: ModelConfig(
        # Fast Processing — generate semantic tags/labels for content
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=512,
    ),
    TaskType.VISUAL_DIAGRAM_DESCRIPTION: ModelConfig(
        # Vision — describe visual diagrams from keyframes
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.2,
        max_tokens=2048,
    ),
    TaskType.OCR_CORRECTION: ModelConfig(
        # Vision — correct OCR output using visual context
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.MARKDOWN_FORMAT: ModelConfig(
        # Fast Processing — format content as proper Markdown
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency="groq/llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.REFERENCE_LINKING: ModelConfig(
        # Fast Processing — link concepts to references/sources
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.HTML_GENERATION: ModelConfig(
        # Fast Processing — generate HTML from structured notes
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=8192,
    ),
    TaskType.PDF_GENERATION: ModelConfig(
        # Code & Math — generate PDF-ready structured content
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.1,
        max_tokens=8192,
    ),

    # ── Phase 7 – Quality Assurance ────────────────────────────────────────

    TaskType.FACT_VERIFICATION: ModelConfig(
        # Complex Reasoning — verify factual accuracy vs transcript
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=4096,
    ),
    TaskType.TRANSCRIPT_CONSISTENCY_CHECK: ModelConfig(
        # Fast Processing — check consistency of transcript with notes
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.OCR_CONSISTENCY_CHECK: ModelConfig(
        # Vision — check OCR output consistency with frame content
        primary=_VISION_PRIMARY,
        secondary=_VISION_SECONDARY,
        emergency=_VISION_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.DUPLICATE_DETECTION: ModelConfig(
        # Embeddings — detect duplicate content via semantic similarity
        primary=_EMBED_PRIMARY,
        secondary=_EMBED_SECONDARY,
        emergency=_EMBED_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),
    TaskType.COMPLETENESS_CHECK: ModelConfig(
        # Complex Reasoning — verify completeness of generated notes
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.ACCURACY_SCORING: ModelConfig(
        # Complex Reasoning — score accuracy of notes vs source
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.READABILITY_SCORING: ModelConfig(
        # Fast Processing — score readability of notes
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=512,
    ),
    TaskType.BIAS_DETECTION: ModelConfig(
        # Complex Reasoning — detect bias in educational content
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.CITATION_VERIFICATION: ModelConfig(
        # Complex Reasoning — verify citations and references
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.GRAMMAR_CHECK: ModelConfig(
        # Fast Processing — grammar and style checking
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=2048,
    ),

    # ── Phase 8 – Search & Retrieval ───────────────────────────────────────

    TaskType.DOCUMENT_EMBEDDING: ModelConfig(
        # Embeddings — embed documents for vector search
        primary=_EMBED_PRIMARY,
        secondary=_EMBED_SECONDARY,
        emergency=_EMBED_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),
    TaskType.EMBEDDING_OPTIMIZATION: ModelConfig(
        # Embeddings — optimize embedding quality and chunking
        primary=_EMBED_PRIMARY,
        secondary=_EMBED_SECONDARY,
        emergency=_EMBED_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),
    TaskType.VECTOR_INDEX_CREATION: ModelConfig(
        # Embeddings — create vector index for retrieval
        primary=_EMBED_PRIMARY,
        secondary=_EMBED_SECONDARY,
        emergency=_EMBED_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),
    TaskType.SEMANTIC_SEARCH_INDEXING: ModelConfig(
        # Embeddings — semantic search index construction
        primary=_EMBED_PRIMARY,
        secondary=_EMBED_SECONDARY,
        emergency=_EMBED_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),
    TaskType.RAG_ANSWERING: ModelConfig(
        # Complex Reasoning — answer questions using RAG retrieval
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),
    TaskType.RAG_DOCUMENT_PREPARATION: ModelConfig(
        # Fast Processing — prepare documents for RAG ingestion
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.0,
        max_tokens=2048,
    ),
    TaskType.KNOWLEDGE_GRAPH_GENERATION: ModelConfig(
        # Complex Reasoning — generate structured knowledge graph
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=4096,
    ),
    TaskType.METADATA_INDEXING: ModelConfig(
        # Embeddings — index metadata fields for search
        primary=_EMBED_PRIMARY,
        secondary=_EMBED_SECONDARY,
        emergency=_EMBED_EMERGENCY,
        temperature=0.0,
        max_tokens=256,
    ),

    # ── Phase 9 – Future Features ───────────────────────────────────────────

    TaskType.PERSONALIZED_LEARNING_META: ModelConfig(
        # Complex Reasoning — generate personalized learning metadata
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.STUDY_PROGRESS_ANALYTICS: ModelConfig(
        # Fast Processing — analyze and report study progress
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency=_FAST_EMERGENCY,
        temperature=0.1,
        max_tokens=2048,
    ),
    TaskType.CONCEPT_RELATIONSHIP_GRAPH: ModelConfig(
        # Complex Reasoning — map relationships between concepts
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.2,
        max_tokens=4096,
    ),
    TaskType.LEARNING_RECOMMENDATION_ENGINE: ModelConfig(
        # Complex Reasoning — generate next-step learning recommendations
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=2048,
    ),
    TaskType.AI_TUTOR_KNOWLEDGE_BASE: ModelConfig(
        # Complex Reasoning — build AI tutor knowledge base
        primary=_COMPLEX_PRIMARY,
        secondary=_COMPLEX_SECONDARY,
        emergency=_COMPLEX_EMERGENCY,
        temperature=0.3,
        max_tokens=4096,
    ),

    # ── Phase 10 – System Management ───────────────────────────────────────

    TaskType.PROMPT_SELECTION: ModelConfig(
        # Code & Math — select optimal prompt for a task
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),
    TaskType.PROMPT_VERSION_MANAGEMENT: ModelConfig(
        # Code & Math — manage and version prompts
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency=_CODE_EMERGENCY,
        temperature=0.1,
        max_tokens=1024,
    ),

    # ── Utility Tasks ──────────────────────────────────────────────────────

    TaskType.JSON_EXTRACTION: ModelConfig(
        # Temperature 0.0 = fully deterministic; JSON accuracy critical
        primary=_FAST_PRIMARY,
        secondary=_FAST_SECONDARY,
        emergency="groq/llama-3.1-8b-instant",
        temperature=0.0,
        max_tokens=1024,
    ),
    TaskType.CODE_GENERATION: ModelConfig(
        # Code & Math — generate production-quality code
        primary=_CODE_PRIMARY,
        secondary=_CODE_SECONDARY,
        emergency="openrouter/qwen/qwen3-coder-480b-a35b:free",
        temperature=0.2,
        max_tokens=8192,
    ),
}


def get_model_config(task: TaskType, user_id: str = None) -> ModelConfig:
    """
    Return the ModelConfig for the given TaskType.
    If an A/B test is registered for the task, probabilistically modifies
    the 'primary' model based on traffic split.

    Usage (from llm_manager.py or any service):
        config = get_model_config(TaskType.TOPIC_DETECTION)

    LLD Reference: §18.4 model_selector.py Reference Implementation
    """
    config = ROUTING_TABLE[task]
    
    experiment = _EXPERIMENT_REGISTRY.get(task)
    if experiment:
        # Determine if we should route to Model B
        route_to_b = False
        if user_id:
            # Deterministic routing based on user_id
            hash_val = int(hashlib.md5(f"{task.name}_{user_id}".encode()).hexdigest(), 16)
            if (hash_val % 10000) / 10000.0 < experiment.traffic_split:
                route_to_b = True
        else:
            # Random routing
            if random.random() < experiment.traffic_split:
                route_to_b = True
                
        if route_to_b:
            # Create a copy so we don't mutate the global ROUTING_TABLE
            return ModelConfig(
                primary=experiment.model_b,
                secondary=config.secondary,
                emergency=config.emergency,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
    return config


def get_primary_model(task: TaskType) -> str:
    """Convenience accessor: returns the primary model ID for a task."""
    return ROUTING_TABLE[task].primary


def get_secondary_model(task: TaskType) -> str:
    """Convenience accessor: returns the secondary model ID for a task."""
    return ROUTING_TABLE[task].secondary


def get_emergency_model(task: TaskType) -> str:
    """Convenience accessor: returns the emergency model ID for a task."""
    return ROUTING_TABLE[task].emergency


def list_all_task_types() -> list[TaskType]:
    """Return all defined task types. Useful for tooling / validation."""
    return list(ROUTING_TABLE.keys())


def get_tasks_by_phase(phase: int) -> list[TaskType]:
    """
    Return all TaskTypes for a given pipeline phase (1-10).
    Phase boundaries match tasks_plan.md T01-T100 groupings.
    """
    phase_ranges = {
        1: list(range(0, 10)),    # T01–T10: Content Preparation
        2: list(range(10, 20)),   # T11–T20: Content Understanding
        3: list(range(20, 35)),   # T21–T35: Knowledge Enrichment
        4: list(range(35, 45)),   # T36–T45: Educational Enhancement
        5: list(range(45, 53)),   # T46–T53: Assessment Generation
        6: list(range(53, 65)),   # T54–T65: Note Organization
        7: list(range(65, 75)),   # T66–T75: Quality Assurance
        8: list(range(75, 83)),   # T76–T82: Search & Retrieval
        9: list(range(83, 88)),   # T83–T90: Future Features
        10: list(range(88, 92)),  # T91–T100: System Management
    }
    all_types = list_all_task_types()
    indices = phase_ranges.get(phase, [])
    return [all_types[i] for i in indices if i < len(all_types)]
