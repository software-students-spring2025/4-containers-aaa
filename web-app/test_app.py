# pylint: disable=redefined-outer-name
"""Test the app for web-app"""

import os
import io
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
import pytest
from app import app, upload_entry, search_entry, update_entry, delete_entry
from pymongo.errors import PyMongoError


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


@patch("app.collection.insert_one")
def test_upload_entry(mock_insert):
    """Test the upload_entry function."""
    # Successful upload
    mock_insert.return_value = MagicMock(acknowledged=True)
    assert upload_entry("test/audio.mp3", {"title": "Test"})

    # Upload with default values
    assert upload_entry("test/audio.mp3")

    # Upload failure (DB error)
    mock_insert.side_effect = PyMongoError()
    assert not upload_entry("test/audio.mp3")

    # No file path provided
    assert not upload_entry("")


# Test delete_entry
@patch("app.collection.delete_one")
def test_delete_entry(mock_delete):
    """Test the delete_entry function."""
    # Successful deletion
    mock_delete.return_value = MagicMock(deleted_count=1)
    assert delete_entry("test/audio.mp3")

    # Deletion failed (no such file)
    mock_delete.return_value = MagicMock(deleted_count=0)
    assert not delete_entry("nonexistent.mp3")

    # No file path or error
    mock_delete.side_effect = PyMongoError()
    assert not delete_entry("")
    assert not delete_entry("test/audio.mp3")


# Test search_entry
@patch("app.collection.find")
def test_search_entry(mock_find):
    """Test the search_entry function."""
    # Successful search with one match
    mock_find.return_value = [
        {"_id": "test/audio.mp3", "title": "Test", "speaker": "John"}
    ]
    assert search_entry(file_path="test")

    # No results found
    mock_find.return_value = []
    assert not search_entry(file_path="missing")

    # Search with multiple fields
    mock_find.return_value = [
        {"_id": "test/audio.mp3", "title": "Test", "speaker": "John"}
    ]
    assert search_entry(file_path="test", title="Test", speaker="John")

    # Error during search
    mock_find.side_effect = PyMongoError()
    assert not search_entry(file_path="error")


# Test update_entry
@patch("app.collection.update_one")
def test_update_entry(mock_update):
    """Test the update_entry function."""
    # Successful update
    mock_update.return_value = MagicMock(modified_count=1)
    assert update_entry("test/audio.mp3", {"title": "Updated"})

    # Update failed (no changes made)
    mock_update.return_value = MagicMock(modified_count=0)
    assert not update_entry("test/audio.mp3", {"title": "No change"})

    # Update error
    mock_update.side_effect = PyMongoError()
    assert not update_entry("test/audio.mp3", {"title": "Error"})
