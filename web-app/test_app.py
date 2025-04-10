# pylint: disable=redefined-outer-name
"""Test the app for web-app"""

import os
import io
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
    edit_entry,
)


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
                "top_words": ["test", "transcript"],
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
    # Create a mock audio file in memory
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
        with patch(
            "app.trigger_ml", return_value={"transcript": "test transcript"}
        ) as mock_trigger_ml:
            response = test_client.post(
                "/upload", data=data, content_type="multipart/form-data"
            )

            assert response.status_code == 200
            assert b"File uploaded successfully" in response.data

            # Verify upload_entry was called
            mock_upload_entry.assert_called_once()

            # Verify trigger_ml was called
            mock_trigger_ml.assert_called_once()

            # Get the file path that was passed to trigger_ml
            actual_filepath = mock_trigger_ml.call_args[0][0]

            # Verify the file was saved
            assert os.path.exists(actual_filepath), "File was not saved"

            # Verify the content of the saved file
            with open(actual_filepath, "rb") as f:
                saved_content = f.read()
                assert (
                    saved_content == mock_audio_content
                ), "File content does not match"


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

    # Update failed (no changes made) - same values
    mock_update.return_value = MagicMock(modified_count=0)
    assert not update_entry("test/audio.mp3", {"title": "No change"})

    # Update failed (no matching document)
    mock_update.return_value = MagicMock(modified_count=0)
    assert not update_entry("nonexistent.mp3", {"title": "New Title"})

    # Update failed (empty update fields)
    mock_update.return_value = MagicMock(modified_count=0)
    assert not update_entry("test/audio.mp3", {})

    # Update failed (non-existent fields)
    mock_update.return_value = MagicMock(modified_count=0)
    assert not update_entry("test/audio.mp3", {"nonexistent_field": "value"})

    # Update error
    mock_update.side_effect = PyMongoError()
    assert not update_entry("test/audio.mp3", {"title": "Error"})


@patch("requests.post")
def test_trigger_ml_success(mock_post):
    """Test trigger_ml function with successful response"""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    expected_data = {"transcript": "test transcript", "message": "success"}
    mock_response.json.return_value = expected_data
    mock_post.return_value = mock_response

    # Test successful case
    result = trigger_ml("test/audio.mp3")
    assert result == expected_data
    mock_post.assert_called_once_with(
        "http://ml-client:6000/get-transcripts",
        json={"audio_file_path": "test/audio.mp3"},
        timeout=10,
    )


@patch("requests.post")
def test_trigger_ml_request_exception(mock_post):
    """Test trigger_ml function with request exception"""
    # Mock request exception
    mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
    result = trigger_ml("test/audio.mp3")
    assert result == "Request exception"


@patch("requests.post")
def test_trigger_ml_connection_error(mock_post):
    """Test trigger_ml function with connection error"""
    # Mock connection error
    mock_post.side_effect = ConnectionError("Connection failed")
    result = trigger_ml("test/audio.mp3")
    assert result == "Connection error"


@patch("requests.post")
def test_trigger_ml_json_response(mock_post):
    """Test trigger_ml function with different JSON responses"""
    test_cases = [
        # Empty response
        {},
        # Response with only message
        {"message": "processing complete"},
        # Response with transcript and other fields
        {"transcript": "hello world", "confidence": 0.95},
        # Response with multiple fields
        {"transcript": "test", "message": "success", "duration": 1.5},
    ]
    for test_data in test_cases:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = test_data
        mock_post.return_value = mock_response

        result = trigger_ml("test/audio.mp3")
        assert result == test_data, f"Failed for test data: {test_data}"


def test_edit_entry():
    """Test the edit_entry function."""

    with patch(
        "app.collection.find_one",
        return_value={
            "_id": "test/audio.mp3",
            "title": "Test Entry",
            "speaker": "Test Speaker",
            "date": "2025-04-01",
            "context": "Test context",
            "transcript": """The rain fell steadily against the windowpane, a soft, persistent 
            drumming. She watched the rain blur the world outside, each drop a tiny, fleeting 
            moment. The sound of the rain created a cozy atmosphere in the room. 
            He loved to walk in the woods, the crunch of leaves under his feet. 
            Every morning, he would walk along the familiar path, observing the changing seasons. 
            A long walk in nature always cleared his head. The old tree stood tall and strong in 
            the center of the field. Generations had gathered under the shade of the tree. 
            They decided to plant another tree nearby, ensuring the legacy continued.""",
            "word_count": 6,
            "top_words": ["test", "transcript"],
            "audio_file": "test/audio.mp3",
            "created_at": "2025-04-01T12:00:00Z",
        },
    ) as mock_find:

        with patch(
            "app.sorted", return_value=[["rain", 3], ["walk", 3], ["tree", 3]]
        ) as mock_sort:
            with patch("app.update_entry", return_value=1) as mock_update:
                response = app.test_client().get("/entry/path/edit")
                assert response.status_code == 200

    mock_find.return_value = {}
    mock_sort.return_value = False
    mock_update.return_value = MagicMock(modified_count=0)
    assert not edit_entry("test/audio.mp3")


def test_view_entry():
    """Test the view_entry route."""
    with patch(
        "app.collection.find_one",
        return_value={
            "_id": "test/audio.mp3",
            "title": "Test Entry",
            "speaker": "Test Speaker",
            "date": "2025-04-01",
            "context": "Test context",
            "transcript": "This is a test transcript",
            "word_count": 6,
            "top_words": ["test", "transcript"],
            "audio_file": "test/audio.mp3",
            "created_at": "2025-04-01T12:00:00Z",
        },
    ) as mock_find_one:

        response = app.test_client().get("/entry/test/audio.mp3")
        assert response.status_code == 200
        assert b"Test Entry" in response.data

    # Test when entry is not found
    mock_find_one.return_value = None
    response = app.test_client().get("/entry/nonexistent.mp3")
    assert response.status_code == 500

    # Upload failure (DB error)
    mock_find_one.side_effect = PyMongoError()
    response = app.test_client().get("/entry/dberror.mp3")
    assert response.status_code == 500


def test_create():
    """Test the create function."""
    response = app.test_client().get("/create")
    assert response.status_code == 200
