import pytest
from pydantic import BaseModel
from services.llm.model_selector import TaskType
from services.llm.validation.registry import SchemaRegistry
from services.llm.validation.schemas.notes import (
    ExamplesOutput,
    FormulasOutput,
    InterviewOutput,
    KeyPointsOutput,
    RelationshipsOutput,
)
from services.llm.validation.schemas.core import GenericTextOutput

def test_registry_new_schemas():
    """Verify that the newly added schemas are correctly mapped."""
    assert SchemaRegistry.get_schema(TaskType.EXAMPLE_EXTRACTION) is ExamplesOutput
    assert SchemaRegistry.get_schema(TaskType.FORMULA_EXPLANATION) is FormulasOutput
    assert SchemaRegistry.get_schema(TaskType.INTERVIEW_PERSPECTIVE) is InterviewOutput
    assert SchemaRegistry.get_schema(TaskType.KEY_POINTS_EXTRACTION) is KeyPointsOutput
    assert SchemaRegistry.get_schema(TaskType.RELATIONSHIP_EXTRACTION) is RelationshipsOutput

def test_registry_fallback():
    """Verify that unmapped schemas fallback to GenericTextOutput."""
    assert SchemaRegistry.get_schema(TaskType.ROUTING) is GenericTextOutput
