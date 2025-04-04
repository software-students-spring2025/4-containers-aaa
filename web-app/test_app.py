"""Test the app for web-app"""

import os
import io
from unittest.mock import patch
from werkzeug.datastructures import FileStorage
import pytest
from app import app

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


def test_upload_provided_audio_file(test_client):
    """Test upload route with a real audio file and metadata"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(
        current_dir,
        "testing_audio",
        "Trump_Short_Speech.mp3",
    )

    # Verify the test audio file exists
    assert os.path.exists(audio_path), f"Test audio file not found at {audio_path}"

    with open(audio_path, "rb") as audio_file:
        file_storage = FileStorage(
            stream=io.BytesIO(audio_file.read()),
            filename="Trump_Short_Speech.mp3",
            content_type="audio/mpeg",
        )
        data = {
            "audio": file_storage,
            "title": "Test Title",
            "speaker": "Trump",
            "date": "2024-01-01",
            "description": "Test Description",
        }

        with patch("app.upload_entry", return_value=True) as mock_upload_entry:
            response = test_client.post(
                "/upload",
                data=data,
                content_type="multipart/form-data",
            )

            assert response.status_code == 200
            assert b"File uploaded successfully" in response.data
            mock_upload_entry.assert_called_once()

