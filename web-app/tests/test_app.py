"""Test the app for web-app"""

import os
import sys
import pytest
from app import app
from werkzeug.datastructures import FileStorage



sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
@pytest.fixture
def test_client():
    """Create a test client for the app"""
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "test_uploads"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.test_client() as client:
        yield client
    # Cleanup after tests
    for file in os.listdir(app.config["UPLOAD_FOLDER"]):
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    os.rmdir(app.config["UPLOAD_FOLDER"])


def test_index_route():
    """Test that the index route returns 200"""
    response = app.test_client().get("/")
    assert response.status_code == 200


def test_create_route():
    """Test that the create route returns 200"""
    response = app.test_client().get("/create")
    assert response.status_code == 200


def test_upload_no_file():
    """Test upload route with no file"""
    response = app.test_client().post("/upload", data={})
    assert response.status_code == 400
    assert b"No audio file" in response.data


def test_upload_empty_file():
    """Test upload route with empty file"""
    data = {"audio": (b"", "")}
    response = app.test_client().post("/upload", data=data)
    assert response.status_code == 400
    assert b"No selected file" in response.data


def test_upload_provided_audio_file():
    """Test upload route with normal audio file"""
    # Create a FileStorage object from the Trump audio file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(
        os.path.dirname(current_dir), "tests", "testing_audio", "Trump_Short_Speech.mp3"
    )
    with open(audio_path, "rb") as f:
        audio_file = FileStorage(
            stream=f, filename="Trump_Short_Speech.mp3", content_type="audio/mpeg"
        )
        data = {
            "audio": audio_file,
            "title": "Test Title",
            "speaker": "Trump",
            "date": "2024-01-01",
            "description": "Test Description",
        }
        response = app.test_client().post("/upload", data=data)
        assert response.status_code == 200
        assert b"File uploaded successfully" in response.data
