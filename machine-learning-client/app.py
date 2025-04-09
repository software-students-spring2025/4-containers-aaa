"""
Flask application for ml client to receive signals from frontend
"""

import os
import re
from collections import Counter
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, OperationFailure
from ml_client import get_transcript


# Load environment variables from .env file
load_dotenv()

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


@app.route("/get-transcripts", methods=["POST"])
def process_transcript_api():
    """
    Receive audio file path from frontend, get transcript from deepgram and update database

    Returns:
        json: message and transcript
    """
    data = request.get_json()
    voice_data_rel_file_path = data.get("audio_file_path")

    print(f"Received file path: {voice_data_rel_file_path}")

    if not voice_data_rel_file_path:
        return jsonify({"message": "No audio file path provided"}), 400

    # Extract just the filename from the path
    filename = os.path.basename(voice_data_rel_file_path)

    # Use the shared volume path
    file_path = os.path.join("/app/uploaded_audio", filename)
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
                        "word_count": word_count(transcript),
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


def parse_transcript(transcript):
    """
    parse transcript string into pairs of word, count
    """
    # parse string into pairs of word, count
    # punctuations removed from consideration
    # e.g. word and word... are treated as the same
    words = re.findall(r"\b\w+\b", transcript.lower())
    freq = Counter(words)
    return [[word, count] for word, count in freq.items()]


def get_word_count(transcript):
    """
    count words in transcript
    """
    words = re.findall(r"\b\w+\b", transcript.lower())
    return len(words)


def rank_by_freq_desc(pairs):
    """
    rank words by frequency descending
    """
    return sorted(pairs, key=lambda x: x[1], reverse=True)


def get_entry(file_path):
    """
    get entry from mongoDB
    """
    entry = collection.find_one({"audio_file": file_path})
    return entry


def trans_to_top_word(transcript):
    """
    1. parse_transcript(transcript)
    2. rank_by_freq_desc(pairs)
    """
    parsed = parse_transcript(transcript)
    ranked = rank_by_freq_desc(parsed)
    return ranked


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
