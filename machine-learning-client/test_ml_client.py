"""Test the ml_client module for machine-learning-client"""

import os
from unittest.mock import patch
from pymongo.errors import PyMongoError
from app import (
    get_word_count,
    rank_by_freq_desc,
    trans_to_top_word,
    count_word_frequency,
    process_transcript_api
)

# Sample test data
SAMPLE_TRANSCRIPT = "This is a sample transcript."
SAMPLE_ERROR_MESSAGE = "Error processing audio file."


def test_sample_audio_fixture(fixture_mock_audio_file):
    """Test mock_audio_file fixture creation."""
    # Check that the file exists
    assert os.path.exists(fixture_mock_audio_file)

    # Check that it's an MP3 file
    assert fixture_mock_audio_file.endswith(".mp3")

    # Check that it has content
    with open(fixture_mock_audio_file, "rb") as f:
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


def test_processs_transcript_api(test_client):
    """Test index route"""

    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("ml_client.get_transcript") as mock_get_transcript:
            mock_get_transcript.return_value = "This is a sample transcript."
            with patch("app.collection.find_one") as mock_find:
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
                with patch("app.collection.update_one") as mock_update:
                    mock_update.return_value = 1
                    response = test_client.post(
                        "/get-transcripts", json={"audio_file_path": "test.mp3"}
                    )

                    mock_exists.assert_called_once()
                    # Check the status code from the response object
                    assert response.status_code == 200

                    mock_update.side_effect = PyMongoError()
                    response = test_client.post(
                        "/get-transcripts", json={"audio_file_path": "test.mp3"}
                    )
                    assert response.status_code == 500

