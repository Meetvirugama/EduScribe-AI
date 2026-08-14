import pytest
from unittest.mock import MagicMock
from services.llm.validation.parser import RawResponseParser, ResponseParseError

def test_parse_valid_response():
    """Test parsing a normal LiteLLM response."""
    mock_raw = MagicMock()
    mock_raw.model = "gpt-4"
    
    mock_choice = MagicMock()
    mock_choice.message.content = "Valid response content"
    mock_choice.finish_reason = "stop"
    
    mock_raw.choices = [mock_choice]
    
    mock_raw.usage = MagicMock()
    mock_raw.usage.prompt_tokens = 10
    mock_raw.usage.completion_tokens = 5
    mock_raw.usage.total_tokens = 15
    
    parsed = RawResponseParser.parse(mock_raw, provider="openai")
    
    assert parsed["content"] == "Valid response content"
    assert parsed["model"] == "gpt-4"
    assert parsed["provider"] == "openai"
    assert parsed["usage"]["prompt_tokens"] == 10
    assert parsed["usage"]["completion_tokens"] == 5
    assert parsed["usage"]["total_tokens"] == 15
    assert parsed["finish_reason"] == "stop"

def test_parse_none_response():
    """Test parsing when LiteLLM returns None (e.g. fatal failure)."""
    with pytest.raises(ResponseParseError, match="LiteLLM returned None"):
        RawResponseParser.parse(None)

def test_parse_empty_choices():
    """Test parsing when choices list is empty."""
    mock_raw = MagicMock()
    mock_raw.choices = []
    
    with pytest.raises(ResponseParseError, match="LiteLLM response contained no choices"):
        RawResponseParser.parse(mock_raw)

def test_parse_none_content():
    """Test parsing when content is None (e.g. content_filter or function call)."""
    mock_raw = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_raw.choices = [mock_choice]
    
    with pytest.raises(ResponseParseError, match="LiteLLM returned None content"):
        RawResponseParser.parse(mock_raw)

def test_parse_usage_as_dict():
    """Test robust usage extraction when usage is a dictionary (common in mocked responses)."""
    mock_raw = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "content"
    mock_raw.choices = [mock_choice]
    
    mock_raw.usage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150
    }
    
    parsed = RawResponseParser.parse(mock_raw)
    assert parsed["usage"]["prompt_tokens"] == 100
    assert parsed["usage"]["completion_tokens"] == 50
    assert parsed["usage"]["total_tokens"] == 150

def test_parse_missing_usage():
    """Test parsing when usage is missing completely."""
    mock_raw = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "content"
    mock_raw.choices = [mock_choice]
    
    # Simulate missing usage entirely
    del mock_raw.usage
    
    parsed = RawResponseParser.parse(mock_raw)
    assert parsed["usage"]["prompt_tokens"] == 0
    assert parsed["usage"]["total_tokens"] == 0

def test_is_truncated():
    """Test truncation detection."""
    parsed_normal = {"finish_reason": "stop"}
    parsed_truncated = {"finish_reason": "length"}
    
    assert not RawResponseParser.is_truncated(parsed_normal)
    assert RawResponseParser.is_truncated(parsed_truncated)
