"""
The main file for the web application.
This file contains the routes for the web application.
"""

import os
from datetime import datetime, timezone
from mutagen.easyid3 import EasyID3
from flask import Flask, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_db_name = os.getenv("MONGO_DB_NAME", "voice_data")

client = MongoClient(f"mongodb://{mongo_username}:{mongo_password}@localhost:{mongo_port}/")
db = client[mongo_db_name]
collection = db["transcriptions"]

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join("web-app", "static", "uploaded_audio")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    """
    Renders the home page of the application.

    Returns:
        str: The rendered HTML template for the index page.
    """
    return render_template("index.html")


@app.route("/create")
def create():
    """
    Renders the create new audio page.

    Returns:
        str: The rendered HTML template for the create page.
    """
    return render_template("create.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Handles the upload of audio files and associated metadata.

    Returns:
        str: A success message if the upload is successful
        tuple: (error message, status code) if the upload fails

    Raises:
        400: If no audio file is provided or if no file is selected
    """
    if "audio" not in request.files:
        return "No audio file", 400

    file = request.files["audio"]
    if file.filename == "":
        return "No selected file", 400

    if file:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
        except (OSError, IOError) as e:
            return "Error saving file", 500

        try:
            title = request.form["title"]
            speaker = request.form["speaker"]
            date = request.form["date"]
            description = request.form["description"]

            audio = EasyID3(filepath)
            audio["title"] = title
            audio["artist"] = speaker
            audio["date"] = date
            audio.save()
        except (OSError, IOError) as e:
            return "Error saving metadata", 500

    return "File uploaded successfully", 200


def upload_entry(file_path, title=None, speaker=None, date=None, context=None, word_count=0, top_words=None):
    """
    Uploads an entry to the MongoDB collection with the given metadata.
    Stores default values if fields are empty or None.
    Returns True if successful, False if failed.
    """
    new_entry = {
        "_id": file_path,
        "title": title or "Untitled",
        "speaker": speaker or "Unknown",
        "date": date or "N/A",
        "context": context or "No context provided",
        "transcript": "",
        "word_count": word_count,
        "top_words": top_words or [],
        "audio_file": file_path,
        "created_at": datetime.now(timezone.utc)
    }

    try:
        result = collection.insert_one(new_entry)
        return result.acknowledged
    except Exception as e:
        return False


def delete_entry(file_path):
    """
    Deletes an entry from the MongoDB collection by file path.
    Returns True if successful, False if no entry was found or failed.
    """
    try:
        result = collection.delete_one({"_id": file_path})
        return result.deleted_count > 0
    except Exception as e:
        return False


def search_entry(file_path=None, title=None, speaker=None):
    """
    Searches for entries in the MongoDB collection based on file path, title, or speaker.
    Performs a partial and case-insensitive match.
    Returns a list of matching documents if found, or False if no matching entries are found.
    """
    query = {}

    if file_path:
        query["_id"] = {"$regex": file_path, "$options": "i"}

    if title:
        query["title"] = {"$regex": title, "$options": "i"}

    if speaker:
        query["speaker"] = {"$regex": speaker, "$options": "i"}

    try:
        results = list(collection.find(query))
        return results if results else False
    except Exception as e:
        return False


def update_entry(file_path, update_fields):
    """
    Updates an existing entry in the MongoDB collection.
    Returns True if update was successful, False if failed.
    """
    try:
        result = collection.update_one(
            {"_id": file_path},
            {"$set": update_fields}
        )
        return result.modified_count > 0
    except Exception as e:
        return False


if __name__ == "__main__":
    app.run(debug=True)
