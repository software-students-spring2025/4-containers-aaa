"""
Flask application for ml client to receive signals from frontend
"""

import os
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
    result = get_transcript(file_path)
    print(f"Transcript result: {result[:100]}...")  # Print first 100 chars

    # Update database
    try:
        # Find the entry by audio_file field
        entry = collection.find_one({"audio_file": voice_data_rel_file_path})
        if entry:
            collection.update_one(
                {"audio_file": voice_data_rel_file_path},
                {"$set": {"transcript": result}},
            )
            print(f"Updated transcript for file: {voice_data_rel_file_path}")
        else:
            print(f"Entry not found for file: {voice_data_rel_file_path}")
            # Try finding by _id
            entry = collection.find_one({"_id": voice_data_rel_file_path})
            if entry:
                collection.update_one(
                    {"_id": voice_data_rel_file_path}, {"$set": {"transcript": result}}
                )
                print(
                    f"Updated transcript for file (by _id): {voice_data_rel_file_path}"
                )
            else:
                print(f"Entry not found by _id either: {voice_data_rel_file_path}")
    except ConnectionFailure as e:
        print(f"MongoDB connection error: {e}")
        return jsonify({"message": "Database connection error"}), 503
    except OperationFailure as e:
        print(f"MongoDB operation error: {e}")
        return jsonify({"message": "Database operation failed"}), 500
    except PyMongoError as e:
        print(f"Other MongoDB error: {e}")
        return jsonify({"message": "Database error occurred"}), 500

    return jsonify({"message": "Transcript updated", "transcript": result}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
