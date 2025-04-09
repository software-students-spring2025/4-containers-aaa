"""Test the ml_client module for machine-learning-client"""

import os
import tempfile
import pytest
# from unittest.mock import patch, MagicMock
# import unittest
# from deepgram import DeepgramClient, PrerecordedOptions
# from ml_client import get_transcript
from app import (
    app,
    get_word_count,
    rank_by_freq_desc,
    trans_to_top_word,
    count_word_frequency,
)

# Sample test data
SAMPLE_TRANSCRIPT = "This is a sample transcript."
SAMPLE_ERROR_MESSAGE = "Error processing audio file."


@pytest.fixture
def mock_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"Mock audio content")
        temp_file_path = temp_file.name

    yield temp_file_path

    # Clean up the file after tests
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


def test_sample_audio_fixture(mock_audio_file):
    """Test mock_audio_file fixture creation."""
    # Check that the file exists
    assert os.path.exists(mock_audio_file)

    # Check that it's an MP3 file
    assert mock_audio_file.endswith(".mp3")

    # Check that it has content
    with open(mock_audio_file, "rb") as f:
        content = f.read()
        assert content == b"Mock audio content"


def test_get_word_count():
    """Test get_transcript function."""
    assert get_word_count(SAMPLE_TRANSCRIPT) == 5
    assert (
        get_word_count(
            "Trying to test this function with punctuation, like this: 'Hello, world!'"
        )
        == 11
    )

    # test with no input
    assert get_word_count("") == 0

    # test with other data types
    assert get_word_count(["This", "is", "a", "sample", "transcript"]) == 0
    assert get_word_count(None) == 0


def test_count_word_frequency():
    """Test count_word_frequency function."""
    assert count_word_frequency(SAMPLE_TRANSCRIPT) == [
        ["this", 1],
        ["is", 1],
        ["a", 1],
        ["sample", 1],
        ["transcript", 1],
    ]
    assert count_word_frequency(
        "Trying to test this function with punctuation, like this: 'Hello, world!'"
    ) == [
        ["trying", 1],
        ["to", 1],
        ["test", 1],
        ["this", 2],
        ["function", 1],
        ["with", 1],
        ["punctuation", 1],
        ["like", 1],
        ["hello", 1],
        ["world", 1],
    ]

    # test with no input
    assert count_word_frequency("") == []

    # test with other data types
    assert count_word_frequency(["This", "is", "a", "sample", "transcript"]) == []
    assert count_word_frequency(None) == []


def test_rank_by_freq_desc():
    """Test rank_by_freq_desc function."""
    assert rank_by_freq_desc(
        [["this", 1], ["is", 1], ["a", 1], ["sample", 1], ["transcript", 1]]
    ) == [["this", 1], ["is", 1], ["a", 1], ["sample", 1], ["transcript", 1]]
    assert rank_by_freq_desc(
        [["this", 1], ["is", 1], ["a", 1], ["sample", 2], ["transcript", 1]]
    ) == [["sample", 2], ["this", 1], ["is", 1], ["a", 1], ["transcript", 1]]

    # test with no input
    assert rank_by_freq_desc([[]]) == []

    # test with invalid input
    assert (
        rank_by_freq_desc(
            [["this", 1], ["is", 1], ["a", 1], ["sample", 2], ["transcript", 1], 1]
        )
        == []
    )
    assert (
        rank_by_freq_desc(
            [["this", 1], ["is", 1], ["transcript", "hello"], ["sample", 2]]
        )
        == []
    )

    # test with other data types
    assert rank_by_freq_desc(["This", "is", "a", "sample", "transcript"]) == []
    assert rank_by_freq_desc(None) == []


def test_trans_to_top_word():
    """Test trans_to_top_word function."""
    assert trans_to_top_word("This is a sample sample transcript.") == [
        ["sample", 2],
        ["this", 1],
        ["is", 1],
        ["a", 1],
        ["transcript", 1],
    ]
    assert trans_to_top_word(
        "Trying to test this function with punctuation, like this: 'Hello, world!'"
    ) == [
        ["this", 2],
        ["trying", 1],
        ["to", 1],
        ["test", 1],
        ["function", 1],
        ["with", 1],
        ["punctuation", 1],
        ["like", 1],
        ["hello", 1],
        ["world", 1],
    ]

    # test with no input
    assert trans_to_top_word("") == []

    # test with other data types
    assert trans_to_top_word(["This", "is", "a", "sample", "transcript"]) == []
    assert trans_to_top_word(None) == []
    assert trans_to_top_word(0) == []


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


# @patch('ml_client.get_transcript')
# @patch('os.path.exists')
# def test_index_route(self, test_client):
#     """Test index route"""

#     with patch("os.path.exists") as mock_exists:
#         mock_exists.return_value = True
#         with patch("ml_client.get_transcript") as mock_get_transcript:
#             mock_get_transcript.return_value = "This is a sample transcript."

#             response = test_client.post("/", json={"audio_file_path": "test.mp3"})
#             mock_get_transcript.assert_called_once()
#             mock_get_transcript.assert_called_once_with(os.path.join
# ("/app/uploaded_audio", "test.mp3"))

#             filepath = os.path.join("/app/uploaded_audio", "test.mp3")
#             print(vars(response))
#             print(vars(response.post()))
#             print()
#             print(vars(mock_get_transcript))
#             print(vars(mock_exists))

#             # assert response.data ["word_count"]== 5

#             assert response == 200
#             # assert response.data == {"transcript": SAMPLE_TRANSCRIPT, "top_words":
# [['this', 1], ['is', 1], ['a', 1], ['sample', 1], ['transcript', 1]], "word_count": 5}

# def test_process_transcript_api():
#     """Test process_transcript_api function."""
#     response = app.test_client().post("/get-transcript")

#     print(response.data)
#     assert response.status_code == 400
#     # with patch("os.path.exists") as mock_exists:
#     #     mock_exists.return_value = True

#     #     with patch("ml_client.get_transcript") as mock_get_transcript:
#     #         mock_get_transcript.return_value = SAMPLE_TRANSCRIPT
