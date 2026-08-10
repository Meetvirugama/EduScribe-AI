import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.content.mindmap import MindmapService
from services.llm.validation.schemas.core import MindMap, MindMapFormat
from schemas.content import LectureInput, Concept
from services.content.context import LectureContext

@pytest.fixture
def mock_llm_manager():
    return AsyncMock()

@pytest.fixture
def base_context():
    input_data = LectureInput(
        transcript="We will discuss microservices. They are independently deployable.",
        segments=[{"text": "We will discuss microservices.", "start": 0.0, "end": 2.0}]
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
async def test_mindmap_generation_valid_response(mock_render, mock_llm_manager, base_context):
    service = MindmapService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    mock_output = MindMap(
        topic="Microservices",
        format=MindMapFormat.MERMAID,
        content="mindmap\n  root((Microservices))\n    Independently deployable"
    )
    mock_llm_manager.generate.return_value = mock_output
    
    result = await service.generate_mindmap(base_context)
    
    assert result["topic"] == "Microservices"
    assert result["format"] == "mermaid"
    assert "Independently deployable" in result["content"]
    
    # Verify template rendering got correct variables
    mock_render.assert_called_once()
    kwargs = mock_render.call_args[1]
    assert "We will discuss microservices." in kwargs["transcript_text"]
    assert "Microservices" in kwargs["concepts_context"]

@pytest.mark.asyncio
async def test_mindmap_generation_llm_exception(mock_llm_manager, base_context):
    service = MindmapService(mock_llm_manager)
    mock_llm_manager.generate.side_effect = Exception("API Error")
    
    result = await service.generate_mindmap(base_context)
    
    assert result["topic"] == ""
    assert result["content"] == ""

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_mindmap_generation_malformed_json(mock_render, mock_llm_manager, base_context):
    service = MindmapService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    from services.llm.validation.schemas.core import GenericTextOutput
    mock_llm_manager.generate.return_value = GenericTextOutput(
        text='Here is your mindmap:\n```json\n{"topic": "Error", "format": "mermaid", "content": "mindmap\\n  root"}\n```'
    )
    
    result = await service.generate_mindmap(base_context)
    
    assert result["topic"] == "Error"
    assert result["content"] == "mindmap\n  root"

@pytest.mark.asyncio
async def test_mindmap_generation_no_llm_manager(empty_context):
    service = MindmapService(llm_manager=None)
    
    result = await service.generate_mindmap(empty_context)
    
    assert result["content"] == ""
