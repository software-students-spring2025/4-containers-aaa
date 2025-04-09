"""
fixture for test_ml_client
"""

import os
import tempfile
import pytest


@pytest.fixture
def fixture_mock_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"Mock audio content")
        temp_file_path = temp_file.name

    yield temp_file_path

    # Clean up the file after tests
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)
