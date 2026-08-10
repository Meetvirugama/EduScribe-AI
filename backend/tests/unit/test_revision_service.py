import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.content.revision import RevisionService
from services.llm.validation.schemas.notes import RevisionSheetOutput, KeyDefinition
from schemas.content import LectureInput, Concept
from services.content.context import LectureContext

@pytest.fixture
def mock_llm_manager():
    return AsyncMock()

@pytest.fixture
def base_context():
    input_data = LectureInput(
        transcript="We will discuss macroeconomics today.",
        segments=[{"text": "We will discuss macroeconomics today.", "start": 0.0, "end": 2.0}]
    )
    ctx = LectureContext(input=input_data)
    ctx.topics = [{"title": "Supply and Demand"}]
    ctx.concepts = [Concept(name="GDP", category="Economics", importance="high")]
    return ctx

@pytest.fixture
def empty_context():
    input_data = LectureInput(transcript="")
    return LectureContext(input=input_data)

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_revision_generation_valid_response(mock_render, mock_llm_manager, base_context):
    service = RevisionService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    mock_output = RevisionSheetOutput(
        title="Revision: Macroeconomics",
        quick_facts=["GDP measures economic health."],
        must_know_points=["Understand supply elasticity."],
        key_definitions=[KeyDefinition(term="GDP", definition="Gross Domestic Product")],
        important_formulas=[],
        priority_topics=["Elasticity"],
        last_minute_tips=[]
    )
    mock_llm_manager.generate.return_value = mock_output
    
    result = await service.generate_revision_sheet(base_context)
    
    assert result["title"] == "Revision: Macroeconomics"
    assert "GDP measures economic health." in result["quick_facts"]
    assert result["key_definitions"][0]["term"] == "GDP"
    assert result["priority_topics"] == ["Elasticity"]
    
    # Verify template rendering got correct variables
    mock_render.assert_called_once()
    kwargs = mock_render.call_args[1]
    assert "macroeconomics" in kwargs["transcript_text"]
    assert "Supply and Demand" in kwargs["topics_context"]
    assert "GDP" in kwargs["concepts_context"]

@pytest.mark.asyncio
async def test_revision_generation_llm_exception(mock_llm_manager, base_context):
    service = RevisionService(mock_llm_manager)
    mock_llm_manager.generate.side_effect = Exception("API Error")
    
    result = await service.generate_revision_sheet(base_context)
    
    assert result["title"] == "Revision Sheet"
    assert result["quick_facts"] == []

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_revision_generation_malformed_json(mock_render, mock_llm_manager, base_context):
    service = RevisionService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    from services.llm.validation.schemas.core import GenericTextOutput
    mock_llm_manager.generate.return_value = GenericTextOutput(
        text='Here is your sheet:\n```json\n{"title": "Error Sheet", "quick_facts": []}\n```'
    )
    
    result = await service.generate_revision_sheet(base_context)
    
    assert result["title"] == "Error Sheet"
    assert result["quick_facts"] == []

@pytest.mark.asyncio
async def test_revision_generation_no_llm_manager(empty_context):
    service = RevisionService(llm_manager=None)
    
    result = await service.generate_revision_sheet(empty_context)
    
    assert result["title"] == "Revision Sheet"
    assert result["quick_facts"] == []
