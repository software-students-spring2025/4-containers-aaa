"""Test the app for web-app"""

import os
from datetime import datetime, timezone
import pytest
from werkzeug.datastructures import FileStorage
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from app import app, delete_entry, update_entry, upload_entry, search_entry

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
mongo_port = os.getenv("MONGO_PORT", "27017")
MONGO_DB_NAME = "voice_data_test"

client = MongoClient(f"mongodb://{mongo_username}:{mongo_password}@localhost:{mongo_port}/")
db = client[MONGO_DB_NAME]
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(os.path.dirname(current_dir), "web-app", "testing_audio", "Trump_Short_Speech.mp3")
    with open(audio_path, "rb") as audio_file:
        file_storage = FileStorage(
            stream=audio_file, filename="Trump_Short_Speech.mp3", content_type="audio/mpeg"
        )
        data = {
            "audio": file_storage,
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
    file_path = "uploads/test_audio.mp3"
    field_value_dict = {
        "title": "Test Title",
        "speaker": "Test Speaker",
        "date": "2024-01-01",
        "context": "Test context",
        "transcript": "This is a test transcript",
        "word_count": 50,
        "top_words": ["test", "audio", "transcript"],
        "audio_file": file_path,
        "created_at": datetime.now(timezone.utc),
    }
    assert upload_entry(file_path, field_value_dict) is True, "Should upload entry successfully"
    assert upload_entry(file_path, field_value_dict) is False, "Should fail to upload duplicate entry"
    assert upload_entry("", {}) is False, "Should fail to upload with empty file path"
    assert upload_entry(None, None) is False, "Should fail to upload with None as file path"


def test_search_entry():
    """Test the search_entry function"""
    file_path = "uploads/test_audio.mp3"
    assert search_entry(file_path=file_path) is not False, "Should find the existing entry"
    assert search_entry(file_path="uploads/nonexistent.mp3") is False, "Should return False for non-existent entry"
    assert search_entry() is not False, "Should return all entries when no criteria are provided"
    assert search_entry(title="Test") is not False, "Should find entries with partial title match"


def test_update_entry():
    """Test the update_entry function"""
    file_path = "uploads/test_audio.mp3"
    update_fields = {"speaker": "Updated Speaker", "context": "Updated context"}
    assert update_entry(file_path, update_fields) is True, "Should update existing entry"
    assert update_entry("uploads/nonexistent.mp3", {"speaker": "New Speaker"}) is False, "Should fail for non-existent entry"
    assert update_entry(file_path, {}) is False, "Should fail to update with empty fields"


def test_delete_entry():
    """Test the delete_entry function"""
    file_path = "uploads/test_audio.mp3"
    assert delete_entry(file_path) is True, "Should delete existing entry"
    assert delete_entry("uploads/nonexistent.mp3") is False, "Should return False for non-existent entry"
    assert delete_entry("") is False, "Should return False for empty file path"
    assert delete_entry(None) is False, "Should return False for None as file path"
