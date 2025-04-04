"""Test the app for web-app"""

import os
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
