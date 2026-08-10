import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from services.content.pipeline import ContentPipeline
from services.content.context import LectureContext
from schemas.content import ServiceStatus

@pytest.fixture
def mock_llm_manager():
    return AsyncMock()

@pytest.mark.asyncio
async def test_pipeline_dag_execution(mock_llm_manager):
    pipeline = ContentPipeline(mock_llm_manager)
    
    # Mock all services to succeed
    pipeline.concept_service.extract_concepts = AsyncMock(return_value={})
    pipeline.notes_service.generate_notes = AsyncMock(return_value={})
    pipeline.flashcard_service.generate_flashcards = AsyncMock(return_value={})
    pipeline.mindmap_service.generate_mindmap = AsyncMock(return_value={})
    pipeline.quiz_service.generate_quiz = AsyncMock(return_value={})
    
    result = await pipeline.generate_full_content("transcript", {})
    
    # Ensure all services were called
    pipeline.concept_service.extract_concepts.assert_called_once()
    pipeline.notes_service.generate_notes.assert_called_once()
    pipeline.flashcard_service.generate_flashcards.assert_called_once()
    pipeline.mindmap_service.generate_mindmap.assert_called_once()
    pipeline.quiz_service.generate_quiz.assert_called_once()
    
    assert result["status"]["concept"] == ServiceStatus.COMPLETED
    assert result["status"]["notes"] == ServiceStatus.COMPLETED

@pytest.mark.asyncio
async def test_pipeline_dag_failure_skips_dependents(mock_llm_manager):
    pipeline = ContentPipeline(mock_llm_manager)
    
    # Mock concept service to fail, meaning level 2 tasks should be skipped
    pipeline.concept_service.extract_concepts = AsyncMock(side_effect=Exception("Concept Error"))
    pipeline.notes_service.generate_notes = AsyncMock(return_value={})
    pipeline.flashcard_service.generate_flashcards = AsyncMock()
    pipeline.mindmap_service.generate_mindmap = AsyncMock()
    pipeline.quiz_service.generate_quiz = AsyncMock()
    
    result = await pipeline.generate_full_content("transcript", {})
    
    assert pipeline.concept_service.extract_concepts.call_count == 2
    pipeline.notes_service.generate_notes.assert_called_once()
    
    # Dependent services should NOT be called
    pipeline.flashcard_service.generate_flashcards.assert_not_called()
    pipeline.mindmap_service.generate_mindmap.assert_not_called()
    pipeline.quiz_service.generate_quiz.assert_not_called()
    
    assert result["status"]["concept"] == ServiceStatus.FAILED
    assert "Concept Error" in result["errors"]["concept"]
