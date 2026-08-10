import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.content.notes import NotesService
from services.llm.validation.schemas.notes import TopicsAndNotesOutput, TopicNote, Citation
from schemas.content import LectureInput
from services.content.context import LectureContext

@pytest.fixture
def mock_llm_manager():
    return AsyncMock()

@pytest.fixture
def base_context():
    input_data = LectureInput(
        transcript="We will discuss microservices today.",
        segments=[{"text": "We will discuss microservices today.", "start": 0.0, "end": 2.0}]
    )
    return LectureContext(input=input_data)

@pytest.fixture
def empty_context():
    input_data = LectureInput(transcript="")
    return LectureContext(input=input_data)

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_notes_generation_valid_response(mock_render, mock_llm_manager, base_context):
    service = NotesService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    mock_output = TopicsAndNotesOutput(
        summary="A summary of microservices.",
        topics=[
            TopicNote(
                title="Microservices Overview",
                start_time="00:00:00",
                end_time="00:01:00",
                notes_markdown="## Microservices\nThey are small.",
                key_takeaways=["Small is good"],
                citations=[Citation(timestamp="00:00:00", source="transcript")]
            )
        ]
    )
    mock_llm_manager.generate.return_value = mock_output
    
    result = await service.generate_notes(base_context)
    
    # Assert result schema
    assert result["summary"] == "A summary of microservices."
    assert len(result["topics"]) == 1
    assert result["topics"][0]["title"] == "Microservices Overview"
    
    # Assert context was populated!
    assert len(base_context.topics) == 1
    assert base_context.topics[0]["title"] == "Microservices Overview"
    
    # Verify template rendering got correct variables
    mock_render.assert_called_once()
    kwargs = mock_render.call_args[1]
    assert "We will discuss microservices today." in kwargs["transcript_text"]

@pytest.mark.asyncio
async def test_notes_generation_llm_exception(mock_llm_manager, base_context):
    service = NotesService(mock_llm_manager)
    mock_llm_manager.generate.side_effect = Exception("API Error")
    
    result = await service.generate_notes(base_context)
    
    assert result["summary"] == "Failed to generate notes."
    assert result["topics"] == []
    assert base_context.topics == []

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_notes_generation_malformed_json(mock_render, mock_llm_manager, base_context):
    service = NotesService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    from services.llm.validation.schemas.core import GenericTextOutput
    mock_llm_manager.generate.return_value = GenericTextOutput(
        text='Here are your notes:\n```json\n{"summary": "Failed to parse", "topics": []}\n```'
    )
    
    result = await service.generate_notes(base_context)
    
    assert result["summary"] == "Failed to parse"
    assert result["topics"] == []

@pytest.mark.asyncio
async def test_notes_generation_no_llm_manager(empty_context):
    service = NotesService(llm_manager=None)
    
    result = await service.generate_notes(empty_context)
    
    assert result["topics"] == []
