# pylint: disable=redefined-outer-name
"""Test the app for web-app"""

import os
import io
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
import pytest
import requests
from pymongo.errors import PyMongoError
from app import (
    app,
    upload_entry,
    search_entry,
    update_entry,
    delete_entry,
    trigger_ml,
)


@pytest.fixture
def test_client():
    """Create a test client for the app"""
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "web-app/testing_audio"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.test_client() as client:
        yield client
    for file in os.listdir(app.config["UPLOAD_FOLDER"]):
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    os.rmdir(app.config["UPLOAD_FOLDER"])


def test_index_route():
    """Test that the index route returns 200"""
    with patch("app.collection.find") as mock_find:
        mock_find.return_value.sort.return_value = [
            {
                "_id": "test/audio.mp3",
                "title": "Test Entry",
                "speaker": "Test Speaker",
                "date": "2025-04-01",
                "context": "Test context",
                "transcript": "This is a test transcript",
                "word_count": 6,
                "top_words": [["test", 2], ["transcript", 1]],
                "audio_file": "test/audio.mp3",
                "created_at": "2025-04-01T12:00:00Z",
            }
        ]
        response = app.test_client().get("/")
        assert response.status_code == 200
        assert b"Test Entry" in response.data


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
    """Test upload route with a mock audio file and metadata"""
    mock_audio_content = b"Mock audio file content for testing"
    file_storage = FileStorage(
        stream=io.BytesIO(mock_audio_content),
        filename="test_audio.mp3",
        content_type="audio/mpeg",
    )
    data = {
        "audio": file_storage,
        "title": "Test Title",
        "speaker": "Test Speaker",
        "date": "2024-01-01",
        "description": "Test Description",
    }

    with patch("app.upload_entry", return_value=True) as mock_upload_entry:
        with patch("app.trigger_ml", return_value={"transcript": "test transcript"}) as mock_trigger_ml:
            response = test_client.post("/upload", data=data, content_type="multipart/form-data")
            assert response.status_code == 200
            assert b"File uploaded successfully" in response.data
            mock_upload_entry.assert_called_once()
            mock_trigger_ml.assert_called_once()
            saved_path = mock_trigger_ml.call_args[0][0]
            assert os.path.exists(saved_path)
            with open(saved_path, "rb") as f:
                assert f.read() == mock_audio_content


@patch("app.collection.insert_one")
def test_upload_entry(mock_insert):
    """Test the upload_entry function."""
    mock_insert.return_value = MagicMock(acknowledged=True)
    assert upload_entry("test/audio.mp3", {"title": "Test"})
    assert upload_entry("test/audio.mp3")
    mock_insert.side_effect = PyMongoError()
    assert not upload_entry("test/audio.mp3")
    assert not upload_entry("")


@patch("app.collection.delete_one")
def test_delete_entry(mock_delete):
    """Test the delete_entry function."""
    mock_delete.return_value = MagicMock(deleted_count=1)
    assert delete_entry("test/audio.mp3")
    mock_delete.return_value = MagicMock(deleted_count=0)
    assert not delete_entry("nonexistent.mp3")
    mock_delete.side_effect = PyMongoError()
    assert not delete_entry("")
    assert not delete_entry("test/audio.mp3")


@patch("app.collection.find")
def test_search_entry(mock_find):
    """Test the search_entry function."""
    mock_find.return_value = [{"_id": "test/audio.mp3", "title": "Test", "speaker": "John"}]
    assert search_entry(file_path="test")
    mock_find.return_value = []
    assert not search_entry(file_path="missing")
    mock_find.return_value = [{"_id": "test/audio.mp3", "title": "Test", "speaker": "John"}]
    assert search_entry(file_path="test", title="Test", speaker="John")
    mock_find.side_effect = PyMongoError()
    assert not search_entry(file_path="error")


@patch("app.collection.update_one")
def test_update_entry(mock_update):
    """Test the update_entry function."""
    mock_update.return_value = MagicMock(modified_count=1)
    assert update_entry("test/audio.mp3", {"title": "Updated"})
    mock_update.return_value = MagicMock(modified_count=0)
    assert not update_entry("test/audio.mp3", {"title": "No change"})
    assert not update_entry("nonexistent.mp3", {"title": "New Title"})
    assert not update_entry("test/audio.mp3", {})
    assert not update_entry("test/audio.mp3", {"nonexistent_field": "value"})
    mock_update.side_effect = PyMongoError()
    assert not update_entry("test/audio.mp3", {"title": "Error"})


@patch("requests.post")
def test_trigger_ml_success(mock_post):
    """Test trigger_ml function with successful response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"transcript": "test transcript", "message": "success"}
    mock_post.return_value = mock_response
    result = trigger_ml("test/audio.mp3")
    assert result == {"transcript": "test transcript", "message": "success"}
    mock_post.assert_called_once()


@patch("requests.post")
def test_trigger_ml_request_exception(mock_post):
    """Test trigger_ml function with request exception"""
    mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
    result = trigger_ml("test/audio.mp3")
    assert result == "Request exception"


@patch("requests.post")
def test_trigger_ml_connection_error(mock_post):
    """Test trigger_ml function with connection error"""
    mock_post.side_effect = ConnectionError("Connection failed")
    result = trigger_ml("test/audio.mp3")
    assert result == "Connection error"


@patch("requests.post")
def test_trigger_ml_json_response(mock_post):
    """Test trigger_ml function with various valid JSON responses"""
    test_cases = [
        {},
        {"message": "processing complete"},
        {"transcript": "hello world", "confidence": 0.95},
        {"transcript": "test", "message": "success", "duration": 1.5},
    ]
    for test_data in test_cases:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = test_data
        mock_post.return_value = mock_response
        result = trigger_ml("test/audio.mp3")
        assert result == test_data


def test_edit_entry_get():
    """Test GET request to the edit_entry route."""
    mock_entry = {
        "_id": "test/audio.mp3",
        "title": "Test Entry",
        "speaker": "Test Speaker",
        "date": "2025-04-01",
        "context": "Test context",
        "transcript": "This is a test transcript",
        "word_count": 6,
        "top_words": [["test", 2], ["transcript", 1]],
        "audio_file": "test/audio.mp3",
        "created_at": datetime.utcnow(),
    }
    with patch("app.collection.find_one", return_value=mock_entry):
        response = app.test_client().get("/entry/test/audio.mp3/edit")
        assert response.status_code == 200
        assert b"Test Entry" in response.data


def test_edit_entry_post():
    """Test POST request to the edit_entry route."""
    mock_entry = {
        "_id": "test/audio.mp3",
        "title": "Old Title",
        "speaker": "Old Speaker",
        "date": "2025-04-01",
        "context": "Old context",
        "transcript": "Old transcript",
        "word_count": 3,
        "top_words": [["old", 1]],
        "audio_file": "test/audio.mp3",
        "created_at": datetime.now(timezone.utc),
    }

    with patch("app.collection.find_one", return_value=mock_entry):
        with patch("app.update_entry", return_value=True) as mock_update:
            response = app.test_client().post(
                "/entry/test/audio.mp3/edit",
                data={
                    "title": "Updated Title",
                    "speaker": "Updated Speaker",
                    "date": "2025-04-01",
                    "context": "Updated context",
                    "transcript": "This is an updated transcript for testing",
                },
            )
            assert response.status_code == 302  # Redirect
            mock_update.assert_called_once()
