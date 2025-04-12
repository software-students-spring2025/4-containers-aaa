"""
Flask application for ml client to receive signals from frontend
"""

import os
import string
from collections import Counter
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, OperationFailure
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)


# Load environment variables from .env file
load_dotenv()

AUDIO_FOLDER = "/app/uploaded_audio"

# local mode
if os.getenv("MODE") == "local":
    # Look for audio files in the web-app's static directory
    AUDIO_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "web-app",
        "static",
        "uploaded_audio",
    )
elif os.getenv("MODE") == "docker":
    AUDIO_FOLDER = "/app/uploaded_audio"

print(f"AUDIO_FOLDER: {AUDIO_FOLDER}")

# Connect to MongoDB
mongo_host = os.getenv(
    "MONGO_HOST", "mongodb"
)  # Use the service name from docker-compose
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_db_name = os.getenv("MONGO_DB_NAME", "voice_data")

client = MongoClient(
    f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/"
)
db = client[mongo_db_name]
collection = db["transcriptions"]


app = Flask(__name__)


STOP_WORDS = {
    "the",
    "is",
    "in",
    "and",
    "of",
    "a",
    "to",
    "with",
    "that",
    "for",
    "on",
    "as",
    "are",
    "at",
    "by",
    "an",
    "be",
    "this",
    "it",
    "from",
    "or",
    "was",
    "we",
    "you",
    "your",
    "they",
    "he",
    "she",
    "but",
    "not",
    "have",
    "has",
    "had",
    "can",
    "will",
    "do",
    "does",
    "did",
    "so",
    "if",
    "then",
    "them",
    "these",
    "those",
    "there",
    "here",
}


@app.route("/get-transcripts", methods=["POST"])
def process_transcript_api():
    """
    Receive audio file path from frontend, get transcript from deepgram and update database

    Returns:
        json: message and transcript
    """
    print("Received transcript request")
    data = request.get_json()
    voice_data_rel_file_path = data.get("audio_file_path")

    print(f"Received file path: {voice_data_rel_file_path}")

    if not voice_data_rel_file_path:
        return jsonify({"message": "No audio file path provided"}), 400

    # Extract just the filename from the path
    filename = os.path.basename(voice_data_rel_file_path)

    # Use the shared volume path
    file_path = os.path.join(AUDIO_FOLDER, filename)
    print(f"Looking for file at: {file_path}")

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found at: {file_path}")
        return jsonify({"message": f"File not found: {file_path}"}), 404

    # Get transcript
    transcript = get_transcript(file_path)
    print(f"Transcript result: {transcript[:100]}...")  # Print first 100 chars

    # Get top words
    top_words = trans_to_top_word(transcript)

    # Get word count
    word_count = get_word_count(transcript)

    # Update database
    try:
        # Find the entry by audio_file field
        entry = collection.find_one({"audio_file": voice_data_rel_file_path})
        if entry:
            collection.update_one(
                {"audio_file": voice_data_rel_file_path},
                {
                    "$set": {
                        "transcript": transcript,
                        "word_count": word_count,
                        "top_words": top_words,
                    }
                },
            )
            print(f"Updated transcript for file: {voice_data_rel_file_path}")
        else:
            print(f"Entry not found for file: {voice_data_rel_file_path}")
    except ConnectionFailure as e:
        print(f"MongoDB connection error: {e}")
        return jsonify({"message": "Database connection error"}), 503
    except OperationFailure as e:
        print(f"MongoDB operation error: {e}")
        return jsonify({"message": "Database operation failed"}), 500
    except PyMongoError as e:
        print(f"Other MongoDB error: {e}")
        return jsonify({"message": "Database error occurred"}), 500

    return jsonify({"message": "Transcript updated", "transcript": transcript}), 200


def get_word_count(transcript):
    """
    count words in transcript
    """
    if not transcript:
        return 0
    if not isinstance(transcript, str):
        return 0
    words = transcript.lower().split()
    return len(words)


def rank_by_freq_desc(pairs):
    """
    rank words by frequency descending
    """
    if not pairs:
        return []
    if not isinstance(pairs, list) or len(pairs) == 0 or pairs[0] == []:
        return []
    if not all((isinstance(item, list) and len(item) == 2) for item in pairs):
        return []
    if not all(isinstance(item[0], str) for item in pairs):
        return []
    if not all(isinstance(item[1], int) for item in pairs):
        return []

    return sorted(pairs, key=lambda x: x[1], reverse=True)


def count_word_frequency(transcript):
    """
    Parse words using spaces and count their frequency, excluding punctuation.

    Args:
        transcript (str): The transcript text to analyze

    Returns:
        list: A list of [word, count] pairs sorted by frequency (descending)
    """
    if not transcript:
        return []
    if not isinstance(transcript, str):
        return []

    words = transcript.lower().split()
    words = [word.strip(string.punctuation) for word in words]
    words = [word for word in words if word]
    freq = Counter(words)

    return [[word, count] for word, count in freq.items()]


def trans_to_top_word(transcript):
    """
    1. count_word_frequency(transcript)
    2. filter out words with length <= 3
    3. rank_by_freq_desc(pairs)
    """
    if not transcript or not isinstance(transcript, str):
        return []
    parsed = count_word_frequency(transcript)
    filtered = [
        [word, count] for word, count in parsed if count > 2 and word not in STOP_WORDS
    ]  # Filter out words that are 3 characters or less
    ranked = rank_by_freq_desc(filtered)
    return ranked


def get_transcript(audio_file: str):
    """
    Async function to transcribe an audio file using the Deepgram API.

    Args:
        audio_file (str): The path to the audio file to transcribe.

    Returns:
        str: The transcript of the audio file.
    """
    try:
        deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
        )

        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
        result = response.results.channels[0].alternatives[0]
        return result.transcript

    except (OSError, IOError) as e:
        return f"File operation error: {e}"
    except KeyError as e:
        return f"API response format error: {e}"
    except RuntimeError as e:
        return f"runtime error: {e}"
    except IndexError as e:
        return f"index error: {e}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
