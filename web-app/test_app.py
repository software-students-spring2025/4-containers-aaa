"""Test the app for web-app"""

import os
import pytest
from werkzeug.datastructures import FileStorage
from app import app, delete_entry, update_entry, upload_entry, search_entry
from datetime import datetime, timezone
from mutagen.easyid3 import EasyID3
from flask import Flask, render_template, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_db_name = "voice_data_test"

client = MongoClient(f"mongodb://{mongo_username}:{mongo_password}@localhost:{mongo_port}/")
db = client[mongo_db_name]
collection = db["transcriptions"]

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


def test_upload_provided_audio_file():
    """Test upload route with normal audio file"""
    # Create a FileStorage object from the Trump audio file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(
        os.path.dirname(current_dir),
        "web-app",
        "testing_audio",
        "Trump_Short_Speech.mp3",
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


def test_upload_entry():
    """Test the upload_entry function"""

    # Test: Valid input
    file_path = "uploads/test_audio.mp3"
    field_value_dict = {
        "title": "Test Title",
        "speaker": "Test Speaker",
        "date": "2024-01-01",
        "context": "Test context",
        "transcript": "This is a test transcript",
        "word_count": 50,
        "top_words": ["test", "audio", "transcript"],
        "audio_file": "uploads/test_audio.mp3",
        "created_at": datetime.now(timezone.utc),
    }
    assert upload_entry(file_path, field_value_dict) is True, "Should upload entry successfully"

    # Test: Duplicate upload with the same file path
    assert upload_entry(file_path, field_value_dict) is False, "Should fail to upload duplicate entry"

    # Test: Empty file path
    file_path = ""
    field_value_dict = {}
    assert upload_entry(file_path, field_value_dict) is False, "Should fail to upload with empty file path"

    # Test: None as file path
    file_path = None
    assert upload_entry(file_path, None) is False, "Should fail to upload with None as file path"


def test_search_entry():
    """Test the search_entry function"""

    # Test: Valid input
    file_path = "uploads/test_audio.mp3"
    result = search_entry(file_path=file_path)
    assert result is not False, "Should find the existing entry"

    # Test: Non-existent entry
    file_path = "uploads/nonexistent.mp3"
    result = search_entry(file_path=file_path)
    assert result is False, "Should return False for non-existent entry"

    # Test: Empty search criteria (should return all entries)
    result = search_entry()
    assert result is not False, "Should return all entries when no criteria are provided"

    # Test: Partial match on title
    title = "Test"
    result = search_entry(title=title)
    assert result is not False, "Should find entries with partial title match"


def test_update_entry():
    """Test the update_entry function"""

    # Test: Valid update
    file_path = "uploads/test_audio.mp3"
    update_fields = {"speaker": "Updated Speaker", "context": "Updated context"}
    assert update_entry(file_path, update_fields) is True, "Should update existing entry"

    # Test: Update non-existent entry
    file_path = "uploads/nonexistent.mp3"
    update_fields = {"speaker": "New Speaker"}
    assert update_entry(file_path, update_fields) is False, "Should fail to update non-existent entry"

    # Test: Invalid field value (empty dictionary)
    file_path = "uploads/test_audio.mp3"
    update_fields = {}
    assert update_entry(file_path, update_fields) is False, "Should fail to update with empty fields"


def test_delete_entry():
    """Test the delete_entry function"""

    # Test: Valid deletion
    file_path = "uploads/test_audio.mp3"
    assert delete_entry(file_path) is True, "Should delete existing entry"

    # Test: Deleting non-existent entry
    file_path = "uploads/nonexistent.mp3"
    assert delete_entry(file_path) is False, "Should return False when deleting non-existent entry"

    # Test: Invalid file path (empty)
    file_path = ""
    assert delete_entry(file_path) is False, "Should return False for empty file path"

    # Test: None as file path
    file_path = None
    assert delete_entry(file_path) is False, "Should return False for None as file path"