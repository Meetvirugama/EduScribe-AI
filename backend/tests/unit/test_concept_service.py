import pytest
from unittest.mock import AsyncMock
from services.content.concept import ConceptService
from services.content.context import LectureContext
from schemas.content import LectureInput
from services.llm.validation.schemas.notes import ConceptsOutput, ConceptItem, SourceReferenceItem

@pytest.fixture
def mock_llm_manager():
    manager = AsyncMock()
    return manager

@pytest.fixture
def base_context():
    input_data = LectureInput(
        transcript="Test transcript",
        segments=[{"text": "Test transcript", "start": 0.0, "end": 10.0}]
    )
    return LectureContext(input=input_data)

@pytest.mark.asyncio
async def test_extract_concepts_valid_response(mock_llm_manager, base_context):
    service = ConceptService(mock_llm_manager)
    
    # Mock LLM returning valid parsed Pydantic schema
    mock_output = ConceptsOutput(
        concepts=[
            ConceptItem(
                name="Test Concept",
                category="General",
                importance="high",
                brief_description="A test description",
                sources=[SourceReferenceItem(chunk_id="chunk_001", timestamp_start=0.0, timestamp_end=10.0)]
            )
        ],
        keywords=["test"],
        key_phrases=["test phrase"]
    )
    mock_llm_manager.generate.return_value = mock_output
    
    result = await service.extract_concepts(base_context)
    
    assert len(result["concepts"]) == 1
    assert result["concepts"][0].name == "Test Concept"
    assert result["concepts"][0].source[0].chunk_id == "chunk_001"
    assert len(base_context.concepts) == 1

@pytest.mark.asyncio
async def test_extract_concepts_llm_exception(mock_llm_manager, base_context):
    service = ConceptService(mock_llm_manager)
    
    # Pre-populate some concepts to ensure they aren't erased
    base_context.concepts = ["Previous Concept"]
    
    mock_llm_manager.generate.side_effect = Exception("API Error")
    
    result = await service.extract_concepts(base_context)
    
    # Existing concepts preserved
    assert result["concepts"] == ["Previous Concept"]

@pytest.mark.asyncio
async def test_extract_concepts_malformed_json(mock_llm_manager, base_context):
    service = ConceptService(mock_llm_manager)
    
    # Simulate string response that couldn't be parsed directly into ConceptsOutput
    from services.llm.validation.schemas.core import GenericTextOutput
    mock_llm_manager.generate.return_value = GenericTextOutput(text="Bad JSON")
    
    result = await service.extract_concepts(base_context)
    
    # Should fallback gracefully to empty
    assert len(result["concepts"]) == 0
