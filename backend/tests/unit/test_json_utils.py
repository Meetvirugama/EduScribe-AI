import pytest
from backend.services.llm.validation.json_utils import JSONExtractor, JSONExtractionError

def test_extract_valid_json():
    """Test extracting a perfectly valid JSON object."""
    valid_json = '{"name": "Physics", "score": 100}'
    result = JSONExtractor.extract_and_repair(valid_json)
    assert result == {"name": "Physics", "score": 100}

def test_extract_fenced_json():
    """Test extracting JSON wrapped in markdown fences."""
    fenced = '```json\n{"name": "Physics"}\n```'
    result = JSONExtractor.extract_and_repair(fenced)
    assert result == {"name": "Physics"}

def test_extract_fenced_with_prose():
    """Test extracting JSON with surrounding prose and fences."""
    prose = '''Here is your output:
```json
{"topic": "Math"}
```
Hope this helps!'''
    result = JSONExtractor.extract_and_repair(prose)
    assert result == {"topic": "Math"}

def test_repair_trailing_comma():
    """Test repairing trailing commas in objects and arrays."""
    trailing_obj = '{"name": "Physics",}'
    assert JSONExtractor.extract_and_repair(trailing_obj) == {"name": "Physics"}
    
    trailing_arr = '{"items": [1, 2, ], "b": 2}'
    assert JSONExtractor.extract_and_repair(trailing_arr) == {"items": [1, 2], "b": 2}

def test_repair_string_corruption_avoidance():
    """Test that the string-aware trailing comma repair does not corrupt commas inside strings."""
    # A naive regex would turn "hello,]" into "hello]" causing a parse failure or data corruption
    safe_string = '{"text": "hello,] \\" , }"}'
    result = JSONExtractor.extract_and_repair(safe_string)
    assert result == {"text": 'hello,] " , }'}

def test_extract_nested_json():
    """Test extraction with deeply nested objects."""
    nested = '{"data": {"items": [{"id": 1, "meta": {"valid": true,}}]}}'
    result = JSONExtractor.extract_and_repair(nested)
    assert result["data"]["items"][0]["meta"]["valid"] is True

def test_unicode_and_escapes():
    """Test that unicode characters and escaped quotes are preserved correctly."""
    # The JSON string contains an escaped quote inside the value, and a mathematical symbol
    unicode_json = '{"formula": "E = mc\\u00b2", "text": "He said \\"hello\\"."}'
    result = JSONExtractor.extract_and_repair(unicode_json)
    assert result["formula"] == "E = mc²"
    assert result["text"] == 'He said "hello".'

def test_enforce_dict_root_type():
    """Test that arrays or primitive values raise a JSONExtractionError."""
    with pytest.raises(JSONExtractionError, match="Expected JSON object, got list"):
        JSONExtractor.extract_and_repair('["a", "b"]')
        
    with pytest.raises(JSONExtractionError, match="Expected JSON object, got str"):
        JSONExtractor.extract_and_repair('"string"')

def test_empty_content():
    """Test that empty or whitespace-only strings fail fast."""
    with pytest.raises(JSONExtractionError, match="Cannot extract JSON from empty content"):
        JSONExtractor.extract_and_repair("")
        
    with pytest.raises(JSONExtractionError, match="Cannot extract JSON from empty content"):
        JSONExtractor.extract_and_repair("   \n  ")

def test_invalid_unrepairable_json():
    """Test that totally invalid JSON correctly raises JSONExtractionError without leaking full content in the message."""
    invalid = '{"name": "Physics", "missing_value": }'
    with pytest.raises(JSONExtractionError, match="Could not extract or repair JSON"):
        JSONExtractor.extract_and_repair(invalid)
