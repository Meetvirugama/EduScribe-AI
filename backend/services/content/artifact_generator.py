import asyncio
import logging
from typing import Dict, Any, List

from .context import LectureContext
from ..llm.llm_manager import LLMManager

from .quiz import QuizGenerator
from .flashcard import FlashcardGenerator
from .mindmap import MindmapGenerator
from .formula import FormulaSheetGenerator
from .interview import InterviewGenerator
from .revision import RevisionGenerator
from .detailed_notes import DetailedNotesGenerator
from services.quality.evaluator import quality_evaluator

logger = logging.getLogger(__name__)

class ArtifactGenerator:
    """
    Dispatches generation of independent artifacts based on the LearningContext.
    These are generated on-demand by the user.
    """
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        
        self.generators = {
            "quiz": QuizGenerator(llm_manager).generate_quiz,
            "flashcards": FlashcardGenerator(llm_manager).generate_flashcards,
            "mindmap": MindmapGenerator(llm_manager).generate_mindmap,
            "formula_sheet": FormulaSheetGenerator(llm_manager).generate_formula_sheet,
            "interview": InterviewGenerator(llm_manager).generate_interview_questions,
            "revision": RevisionGenerator(llm_manager).generate_revision_sheet,
            "detailed_notes": DetailedNotesGenerator(llm_manager).generate_detailed_notes,
        }

    async def generate(self, context: LectureContext, artifacts_to_generate: List[str]) -> Dict[str, Any]:
        """
        Generate multiple artifacts in parallel.
        """
        logger.info(f"Generating artifacts: {artifacts_to_generate}")
        
        tasks = []
        keys = []
        
        for artifact in artifacts_to_generate:
            if artifact in self.generators:
                tasks.append(self.generators[artifact](context))
                keys.append(artifact)
            else:
                logger.warning(f"Unknown artifact type requested: {artifact}")
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate {key}: {result}")
                output[key] = None
            else:
                # Evaluate artifact quality
                quality_report = quality_evaluator.evaluate_artifact(
                    artifact_type=key,
                    artifact_data=result,
                    transcript_text=context.transcript,
                    concepts=context.concepts
                )
                
                output[key] = {
                    "data": result,
                    "quality": quality_report.to_dict()
                }
                
        return output
