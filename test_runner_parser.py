import sys
import pytest
from unittest.mock import MagicMock
sys.modules['backend.services.youtube'] = MagicMock()
sys.modules['backend.services.audio'] = MagicMock()
sys.modules['backend.services.audio.service'] = MagicMock()

pytest.main(["backend/tests/unit/test_parser.py"])
