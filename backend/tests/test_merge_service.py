import pytest
import uuid
from unittest.mock import patch, MagicMock

from services.merge_service import MergeService

@pytest.fixture
def merge_service():
    return MergeService()

def test_format_time(merge_service):
    assert merge_service._format_time(0) == "00:00"
    assert merge_service._format_time(59) == "00:59"
    assert merge_service._format_time(60) == "01:00"
    assert merge_service._format_time(3600) == "01:00:00"
    assert merge_service._format_time(3665) == "01:01:05"

@patch("services.merge_service.AsyncSessionLocal")
@patch("os.path.exists")
@pytest.mark.asyncio
async def test_generate_merged_markdown_no_transcript(mock_exists, mock_session, merge_service):
    # Mock exists to return False
    mock_exists.return_value = False
    
    # Mock DB session and execution
    mock_db = MagicMock()
    mock_session.return_value.__aenter__.return_value = mock_db
    
    # Mock transcript fetch returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = await merge_service.generate_merged_markdown(str(uuid.uuid4()))
    assert result is None
