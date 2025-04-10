"""
fixture for test_ml_client
"""

import os
import tempfile
import pytest
from app import app


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

@pytest.fixture
def test_client():
    """Create a test client for the app"""
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "web-app/testing_audio"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.test_client() as client:
        yield client
    # Cleanup after tests
    for file in os.listdir(app.config["UPLOAD_FOLDER"]):
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    os.rmdir(app.config["UPLOAD_FOLDER"])
