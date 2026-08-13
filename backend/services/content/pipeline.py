"""
services/content/pipeline.py — EduScribe AI Content Pipeline

Enforces the 4-phase data flow defined in the pipeline architecture:

    Phase 1: Transcript + Vision → Unified Markdown (unified_md)
    Phase 2: unified_md → Parallel extractions (concepts, definitions,
             formulas, keywords, relations, examples, topics)
    Phase 3: All Phase 2 outputs → Detailed Learning Note (detailed_notes_md)
    Phase 4: detailed_notes_md → User-chosen artifacts (quiz, flashcards,
             mindmap, revision, interview) — ON DEMAND via ArtifactGenerator

Architecture rules:
  • Phase 1 must complete before Phase 2 starts.
  • Phase 3 must complete before Phase 4 starts.
  • Phase 4 is NEVER run automatically; it is triggered on-demand by the user.
  • All artifact generators (Phase 4) MUST read from detailed_notes_md only.
"""
import asyncio
import logging


from .context import LectureContext
from ..llm.llm_manager import LLMManager
from schemas.content import LectureInput, ServiceStatus

from services.merge.models import MergedLecture

from .markdown_builder import build_unified_markdown
from .topic import TopicService
from .concept import ConceptService
from .definition import DefinitionService
from .example import ExampleService
from .key_point import KeyPointService
from .relationship import RelationshipService
from .formula import FormulaSheetGenerator
from .detailed_notes import DetailedNotesGenerator

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Orchestrates Phase 1 → Phase 2 → Phase 3 of the learning pipeline.

    Phase 4 (artifact generation) is intentionally excluded here and handled
    on-demand by ArtifactGenerator in artifact_generator.py.
    """

    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager

        # Phase 2 — Extraction services
        self.topic_service = TopicService(llm_manager)
        self.concept_service = ConceptService(llm_manager)
        self.definition_service = DefinitionService(llm_manager)
        self.example_service = ExampleService(llm_manager)
        self.key_point_service = KeyPointService(llm_manager)
        self.relationship_service = RelationshipService(llm_manager)
        self.formula_service = FormulaSheetGenerator(llm_manager)

        # Phase 3 — Knowledge compiler
        self.detailed_notes_generator = DetailedNotesGenerator(llm_manager)

    async def build_learning_context(
            self, merged_lecture: MergedLecture) -> LectureContext:
        """
        Execute Phase 1 → Phase 2 → Phase 3 sequentially.
        Returns the fully populated LectureContext (with detailed_notes_md).
        """
        logger.info(
            f"Starting content pipeline for video {merged_lecture.video_id}")

        # ── Build initial context ────────────────────────────────────────────
        lecture_input = LectureInput(
            transcript=merged_lecture.full_transcript_text,
            metadata=merged_lecture.metadata,
            segments=merged_lecture.all_transcript_segments,
            frames=[
                {
                    "path": f.frame_path,
                    "time_sec": f.timestamp_sec,
                    "ocr": f.ocr_text,
                    "scene_number": f.scene_number
                }
                for f in merged_lecture.all_frames
            ]
        )
        context = LectureContext(input=lecture_input)

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 1: Build Unified Markdown
        # Merges transcript segments + vision frames (OCR) into a single,
        # structured Markdown document. Stored in context.unified_md.
        # ══════════════════════════════════════════════════════════════════════
        logger.info("Phase 1: Building Unified Markdown...")
        context.unified_md = build_unified_markdown(
            segments=merged_lecture.all_transcript_segments,
            frames=[
                {
                    "time_sec": f.timestamp_sec,
                    "ocr": f.ocr_text or "",
                    "scene_number": f.scene_number
                }
                for f in merged_lecture.all_frames
            ],
            metadata=merged_lecture.metadata,
        )
        logger.info(
            f"Phase 1 complete: unified_md ({len(context.unified_md)} chars)")

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 2: Parallel Extractions
        # All services read from context.unified_md (via transcript/segments).
        # Run topic, concept, definition, example, key_point, formula
        # concurrently, then run relationship (depends on concepts).
        # ══════════════════════════════════════════════════════════════════════
        logger.info("Phase 2: Running parallel extractions...")
        await asyncio.gather(
            self.topic_service.execute_with_retry(
                "topic", context, self.topic_service.extract_topics, context),
            self.concept_service.execute_with_retry(
                "concept", context, self.concept_service.extract_concepts, context),
            self.definition_service.execute_with_retry(
                "definition", context, self.definition_service.extract_definitions, context),
            self.example_service.execute_with_retry(
                "example", context, self.example_service.extract_examples, context),
            self.key_point_service.execute_with_retry(
                "key_point", context, self.key_point_service.extract_key_points, context),
            self.formula_service.execute_with_retry(
                "formula", context, self.formula_service.generate_formula_sheet, context),
        )

        # Relationship extraction depends on concepts being available
        if context.status.get("concept") == ServiceStatus.COMPLETED:
            await self.relationship_service.execute_with_retry(
                "relationship", context,
                self.relationship_service.extract_relationships, context
            )
        else:
            logger.warning(
                "Phase 2: Skipping relationship extraction — concepts failed.")

        logger.info("Phase 2 complete.")

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 3: Detailed Learning Note
        # Compiles ALL Phase 2 extractions into a single rich learning note.
        # Stored in context.detailed_notes_md.
        # This is the ONLY input that Phase 4 artifact generators will use.
        # ══════════════════════════════════════════════════════════════════════
        logger.info("Phase 3: Compiling Detailed Learning Note...")
        await self.detailed_notes_generator.execute_with_retry(
            "detailed_notes", context,
            self.detailed_notes_generator.generate_detailed_notes, context
        )
        logger.info(
            f"Phase 3 complete: detailed_notes_md ({len(context.detailed_notes_md)} chars)"
        )

        return context
