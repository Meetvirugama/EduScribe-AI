import pytest
from unittest.mock import AsyncMock, patch
from services.content.formula import FormulaService
from services.llm.validation.schemas.notes import FormulasOutput, FormulaItem
from schemas.content import LectureInput
from services.content.context import LectureContext

@pytest.fixture
def mock_llm_manager():
    return AsyncMock()

@pytest.fixture
def base_context():
    input_data = LectureInput(
        transcript="Test transcript",
        segments=[{"text": "So F equals ma.", "start": 83.0, "end": 85.0}],
        frames=[{"ocr": "F = ma", "time_sec": 83.0}]
    )
    return LectureContext(input=input_data)

@pytest.fixture
def empty_context():
    input_data = LectureInput(
        transcript="",
        segments=[],
        frames=[]
    )
    return LectureContext(input=input_data)

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_formula_extraction_valid_response(mock_render, mock_llm_manager, base_context):
    service = FormulaService(mock_llm_manager)
    
    # Mock render so we don't depend on actual file system template
    mock_render.return_value = "Mock Prompt"
    
    mock_output = FormulasOutput(
        formulas=[
            FormulaItem(
                name="Newton's Second Law",
                expression="F = ma",
                variables={"F": "Force", "m": "Mass", "a": "Acceleration"},
                context="Used to calculate force",
                source="both",
                timestamp="00:01:23"
            )
        ],
        notation_guide={"F": "Force"},
        topic_groups={"Physics": ["Newton's Second Law"]}
    )
    mock_llm_manager.generate.return_value = mock_output
    
    result = await service.generate_formula_sheet(base_context)
    
    assert len(result["formulas"]) == 1
    assert result["formulas"][0]["name"] == "Newton's Second Law"
    assert result["formulas"][0]["timestamp"] == "00:01:23"
    assert "Physics" in result["topic_groups"]
    
    # Verify template rendering got correct variables
    mock_render.assert_called_once()
    kwargs = mock_render.call_args[1]
    assert "[00:01:23] So F equals ma." in kwargs["transcript_context"]
    assert "[00:01:23] (slide): F = ma" in kwargs["ocr_context"]

@pytest.mark.asyncio
async def test_formula_extraction_llm_exception(mock_llm_manager, base_context):
    service = FormulaService(mock_llm_manager)
    mock_llm_manager.generate.side_effect = Exception("API Error")
    
    # _safe_dump handles the fallback properly if exception thrown before it?
    # Actually wait, FormulaService wraps generation in try-except block 
    # and returns empty_result on Exception.
    result = await service.generate_formula_sheet(base_context)
    
    assert result["formulas"] == []
    assert result["notation_guide"] == {}
    assert result["topic_groups"] == {}

@pytest.mark.asyncio
@patch("services.content.base.PromptManager.render")
async def test_formula_extraction_malformed_json(mock_render, mock_llm_manager, base_context):
    service = FormulaService(mock_llm_manager)
    mock_render.return_value = "Mock Prompt"
    
    from services.llm.validation.schemas.core import GenericTextOutput
    # Simulating the fallback to raw JSON string with some extra text
    mock_llm_manager.generate.return_value = GenericTextOutput(
        text='Here are the formulas:\n```json\n{"formulas": [], "notation_guide": {}, "topic_groups": {}}\n```'
    )
    
    result = await service.generate_formula_sheet(base_context)
    
    assert result["formulas"] == []
    assert result["notation_guide"] == {}
    assert result["topic_groups"] == {}

@pytest.mark.asyncio
async def test_formula_extraction_no_llm_manager(empty_context):
    service = FormulaService(llm_manager=None)
    
    result = await service.generate_formula_sheet(empty_context)
    
    assert result["formulas"] == []

def test_ocr_math_detector_filtering():
    service = FormulaService()
    
    # Should detect as math
    assert service._is_math_formula("E = mc²")
    assert service._is_math_formula("F = ma")
    assert service._is_math_formula("y = mx + b")
    assert service._is_math_formula("x + y = 10")
    assert service._is_math_formula("area = width * height")
    assert service._is_math_formula("∫ x dx")
    assert service._is_math_formula("A = πr²")
    
    # Should NOT detect as math
    assert not service._is_math_formula("Non-linear regression - introduction")
    assert not service._is_math_formula("1. Introduction")
    assert not service._is_math_formula("A - B - C")
    assert not service._is_math_formula("User-centric design")
