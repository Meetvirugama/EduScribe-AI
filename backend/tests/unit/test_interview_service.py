import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.content.interview import InterviewService
from services.llm.validation.schemas.notes import InterviewOutput, TechnicalQuestion, ConceptualQuestion
from schemas.content import LectureInput, Concept
from services.content.context import LectureContext

@pytest.fixture
def mock_llm_manager():
    return AsyncMock()

@pytest.fixture
def base_context():
    input_data = LectureInput(
        transcript="We will discuss microservices. They are independently deployable.",
        segments=[{"text": "We will discuss microservices.", "start": 0.0, "end": 2.0}],
        difficulty=4
    )
    ctx = LectureContext(input=input_data)
    ctx.concepts = [Concept(name="Microservices", category="Architecture", importance="high")]
    return ctx

@pytest.fixture
def empty_context():
    input_data = LectureInput(transcript="")
    return LectureContext(input=input_data)

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_interview_extraction_valid_response(mock_render, mock_llm_manager, base_context):
    service = InterviewService(mock_llm_manager)
    
    mock_render.return_value = "Mock Prompt"
    
    mock_output = InterviewOutput(
        technical_questions=[
            TechnicalQuestion(
                question="What is a microservice?",
                expected_answer_points=["Independently deployable"],
                difficulty="medium",
                topic="Microservices"
            )
        ],
        conceptual_questions=[],
        scenario_questions=[],
        viva_questions=[],
        difficulty_breakdown={"easy": 0, "medium": 1, "hard": 0}
    )
    mock_llm_manager.generate.return_value = mock_output
    
    result = await service.generate_interview_questions(base_context)
    
    assert len(result["technical_questions"]) == 1
    assert result["technical_questions"][0]["question"] == "What is a microservice?"
    assert result["difficulty_breakdown"]["medium"] == 1
    
    # Verify template rendering got correct variables
    mock_render.assert_called_once()
    kwargs = mock_render.call_args[1]
    assert "We will discuss microservices." in kwargs["transcript_text"]
    assert "Microservices" in kwargs["concepts_context"]
    assert kwargs["difficulty"] == "hard"  # mapped from input.difficulty=4

@pytest.mark.asyncio
async def test_interview_extraction_llm_exception(mock_llm_manager, base_context):
    service = InterviewService(mock_llm_manager)
    mock_llm_manager.generate.side_effect = Exception("API Error")
    
    result = await service.generate_interview_questions(base_context)
    
    assert result["technical_questions"] == []
    assert result["conceptual_questions"] == []
    assert result["viva_questions"] == []

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_interview_extraction_malformed_json(mock_render, mock_llm_manager, base_context):
    service = InterviewService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    from services.llm.validation.schemas.core import GenericTextOutput
    mock_llm_manager.generate.return_value = GenericTextOutput(
        text='Here are the questions:\n```json\n{"technical_questions": [], "conceptual_questions": [], "scenario_questions": [], "viva_questions": []}\n```'
    )
    
    result = await service.generate_interview_questions(base_context)
    
    assert result["technical_questions"] == []
    assert result["conceptual_questions"] == []
    assert result["viva_questions"] == []

@pytest.mark.asyncio
async def test_interview_extraction_no_llm_manager(empty_context):
    service = InterviewService(llm_manager=None)
    
    result = await service.generate_interview_questions(empty_context)
    
    assert result["technical_questions"] == []
