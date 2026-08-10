import sys
import pytest

# Mock out the problematic modules that fail due to missing dependencies
import sys
from unittest.mock import MagicMock
sys.modules['backend.services.youtube'] = MagicMock()
sys.modules['backend.services.audio'] = MagicMock()
sys.modules['backend.services.audio.service'] = MagicMock()

pytest.main(["backend/tests/unit/test_json_utils.py"])
