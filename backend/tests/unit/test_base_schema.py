import pytest
from pydantic import ValidationError
from services.llm.validation.base_schema import BaseLLMOutput

def test_base_schema_defaults_and_ignored_extras():
    """Verify that defaults are populated and extra fields are safely ignored."""
    # Simulate LLM returning an empty dict (or hallucinating fields)
    raw_json = {"hallucinated_key": "some_value"}
    
    output = BaseLLMOutput.model_validate(raw_json)
    
    # Assert defaults were correctly applied
    assert output.provider == "unknown"
    assert output.model == "unknown"
    assert output.latency == 0.0
    assert output.total_tokens == 0
    assert output.schema_version == "1.0"
    assert output.confidence == 1.0
    assert output.created_at > 0  # timestamp was generated
    
    # Assert extra field was stripped
    assert not hasattr(output, "hallucinated_key")

def test_base_schema_confidence_constraints():
    """Verify the confidence field strictly enforces ge=0.0 and le=1.0."""
    
    # Valid confidence
    output = BaseLLMOutput.model_validate({"confidence": 0.85})
    assert output.confidence == 0.85
    
    output_low = BaseLLMOutput.model_validate({"confidence": 0.0})
    assert output_low.confidence == 0.0
    
    output_high = BaseLLMOutput.model_validate({"confidence": 1.0})
    assert output_high.confidence == 1.0
    
    # Invalid confidence (too low)
    with pytest.raises(ValidationError) as exc_info:
        BaseLLMOutput.model_validate({"confidence": -0.1})
    assert "Input should be greater than or equal to 0" in str(exc_info.value)
    
    # Invalid confidence (too high)
    with pytest.raises(ValidationError) as exc_info:
        BaseLLMOutput.model_validate({"confidence": 1.1})
    assert "Input should be less than or equal to 1" in str(exc_info.value)

def test_base_schema_immutability():
    """Verify that the model is frozen and cannot be mutated directly."""
    output = BaseLLMOutput()
    
    with pytest.raises(ValidationError) as exc_info:
        output.provider = "changed"
    
    assert "Instance is frozen" in str(exc_info.value)

def test_base_schema_metadata_injection_via_model_copy():
    """Verify that LLMManager's metadata injection pattern correctly generates a new updated instance."""
    original = BaseLLMOutput()
    original_created_at = original.created_at
    
    # Simulate LLMManager metadata injection
    updated = original.model_copy(update={
        "provider": "google",
        "model": "gemini-2.5-flash",
        "latency": 1.25,
        "total_tokens": 150
    })
    
    # Verify the original remains unchanged (frozen contract intact)
    assert original.provider == "unknown"
    assert original.latency == 0.0
    
    # Verify the new instance has the updated fields
    assert updated.provider == "google"
    assert updated.model == "gemini-2.5-flash"
    assert updated.latency == 1.25
    assert updated.total_tokens == 150
    
    # Verify non-updated fields carried over
    assert updated.confidence == 1.0
    assert updated.schema_version == "1.0"
    assert updated.created_at == original_created_at

class MockTaskOutput(BaseLLMOutput):
    """Mock subclass for testing serialization of custom outputs."""
    summary: str
    points: list[str]

def test_subclass_serialization():
    """Verify that a subclass correctly serializes both its own fields and the inherited metadata."""
    
    # Simulate LLM returning task data
    raw_llm_json = {
        "summary": "This is a summary.",
        "points": ["Point A", "Point B"],
        "extra_garbage": True
    }
    
    # 1. Validation stage
    validated = MockTaskOutput.model_validate(raw_llm_json)
    
    # 2. Metadata injection stage
    final_output = validated.model_copy(update={
        "provider": "openrouter",
        "model": "deepseek-v3",
        "latency": 2.5
    })
    
    # 3. Serialization stage (as consumed by the frontend API)
    serialized = final_output.model_dump()
    
    expected_subset = {
        "summary": "This is a summary.",
        "points": ["Point A", "Point B"],
        "provider": "openrouter",
        "model": "deepseek-v3",
        "latency": 2.5,
        "total_tokens": 0,  # default
        "confidence": 1.0,  # default
        "schema_version": "1.0" # default
    }
    
    # Verify all expected keys are present and match
    for key, val in expected_subset.items():
        assert serialized[key] == val
        
    # Verify created_at is present
    assert "created_at" in serialized
    assert serialized["created_at"] > 0
    
    # Verify extra fields were stripped
    assert "extra_garbage" not in serialized
