"""
The main file for the web application.
This file contains the routes for the web application.
"""

import os
import re
from datetime import datetime, timezone
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import requests


# Load environment variables from .env file
load_dotenv()


# Connect to MongoDB
ML_CLIENT_URL = os.getenv("ML_CLIENT_URL", "http://ml-client:6000/get-transcripts")
if os.getenv("MODE") == "docker":
    ML_CLIENT_URL = os.getenv("ML_CLIENT_URL", "http://ml-client:6000/get-transcripts")
elif os.getenv("MODE") == "local":
    ML_CLIENT_URL = os.getenv("ML_CLIENT_URL", "http://localhost:6000/get-transcripts")

print(f"ML_CLIENT_URL: {ML_CLIENT_URL}")
mongo_host = os.getenv("MONGO_HOST", "mongodb")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
mongo_db_name = os.getenv("MONGO_DB_NAME", "voice_data")

client = MongoClient(
    f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/"
)
db = client[mongo_db_name]
collection = db["transcriptions"]

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploaded_audio")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size

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

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main index route. Renders the list of entries.
    Supports keyword search via POST.
    """
    keyword = ""
    try:
        if request.method == "POST":
            keyword = request.form.get("keyword", "").strip()
            query = {
                "$or": [
                    {"title": {"$regex": keyword, "$options": "i"}},
                    {"speaker": {"$regex": keyword, "$options": "i"}},
                    {"date": {"$regex": keyword, "$options": "i"}},
                ]
            }
            entries = list(collection.find(query).sort("created_at", -1))
        else:
            entries = list(collection.find().sort("created_at", -1))

        return render_template("index.html", entries=entries, keyword=keyword)

    except PyMongoError as e:
        print("Search error:", e)
        return "Internal Server Error", 500


@app.route("/entry/<path:file_path>")
def view_entry(file_path):
    """
    Renders a detail page for a specific entry using its file path (_id).
    """
    try:
        entry = collection.find_one({"_id": file_path})
        if entry is None:
            return "Entry not found", 500
        return render_template("detail.html", entry=entry)
    except PyMongoError:
        return "Database error", 500


@app.route("/delete/<path:file_path>", methods=["POST"])
def delete_route(file_path):
    """
    Deletes an entry from MongoDB using its file path (_id).
    """
    if delete_entry(file_path):
        return redirect(url_for("index"))
    return "Delete failed", 500


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

    This route processes POST requests containing:
    - An audio file
    - Form data including title, speaker, date, and description

    Returns:
        str: A success message if the upload is successful
        tuple: (error message, status code) if the upload fails

    Raises:
        400: If no audio file is provided or if no file is selected
    """
    # check if the audio file is provided
    if "audio" not in request.files:
        return "No audio file", 400

    file = request.files["audio"]
    if file.filename == "":
        return "No selected file", 400

    # save the file to the uploads folder in the root directory
    if file:
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            print("filename:", filename)
            print("filepath:", filepath)
            file.save(filepath)
        except (OSError, IOError) as e:
            print("Error saving file:", e)
            return "Error saving file", 500

        # get data from the form
        try:
            title = request.form["title"]
            speaker = request.form["speaker"]
            date = request.form["date"]
            description = request.form["description"]
            print("Got data from page:", title, speaker, date, description)
            # Prepare metadata dictionary
            metadata = {
                "title": title,
                "speaker": speaker,
                "date": date,
                "context": description,
            }

            # Try to send to ML for transcript
            try:
                print(f"Sending file to ML client: {filepath}")
                ml_response = trigger_ml(filepath)
                print(f"ML client response: {ml_response}")
                transcript = ml_response.get("transcript", "")
                metadata["transcript"] = transcript
            except requests.exceptions.RequestException as e:
                print("Error from ML:", e)
                metadata["transcript"] = ""

            # Save metadata using upload_entry function
            if not upload_entry(filepath, metadata):
                print("Error uploading entry to MongoDB")
                return "Error saving metadata to database", 500

        except (OSError, IOError) as e:
            print("Error during data processing:", e)
            return "Error during data processing", 500

    return "File uploaded successfully", 200


@app.route("/entry/<path:file_path>/edit", methods=["GET", "POST"])
def edit_entry(file_path):
    """
    Renders a edit page for a specific entry for user to edit any info except audio in database.
    """
    try:
        entry = collection.find_one({"_id": file_path})
        if not entry:
            return False

        if request.method == "POST":
            updated_fields = {
                "title": request.form["title"],
                "speaker": request.form["speaker"],
                "date": request.form["date"],
                "context": request.form["context"],
                "transcript": request.form["transcript"],
            }
            updated_fields["word_count"] = len(updated_fields["transcript"].split())
            updated_fields["top_words"] = sorted(
                [
                    (word, count)
                    for word, count in Counter(
                        re.findall(r"\b\w+\b", updated_fields["transcript"].lower())
                    ).items()
                    if len(word) > 2 and word not in STOP_WORDS
                ],
                key=lambda x: x[1],
                reverse=True,
            )
            update_entry(file_path, updated_fields)
            return redirect(url_for("view_entry", file_path=file_path))
        return render_template("edit.html", entry=entry)
    except PyMongoError:
        return False


def upload_entry(file_path, field_value_dict=None):
    """
    Uploads an entry to the MongoDB collection with the given metadata.
    Stores default values if fields are empty or None.
    Returns True if successful, False if failed.

    Args:
        file_path (str): The file path of the audio file.
        field_value_dict (dict): A dictionary containing metadata fields and their values.

    Returns:
        bool: True if the entry was uploaded successfully, False otherwise.
    """
    if not file_path:
        return False

    if field_value_dict is None:
        field_value_dict = {}

    transcript = field_value_dict.get("transcript", "")
    word_count = len(transcript.split())

    # Filter and rank top words (longer than 3 characters)
    top_words = sorted(
        [
            (word, count)
            for word, count in Counter(
                re.findall(r"\b\w+\b", transcript.lower())
            ).items()
            if len(word) > 3 and word not in STOP_WORDS
        ],
        key=lambda x: x[1],
        reverse=True,
    )
    # store computed values into dic
    field_value_dict["word_count"] = word_count
    field_value_dict["top_words"] = top_words
    # Create a new entry with default values or values from the dictionary
    new_entry = {
        "_id": file_path,
        "title": field_value_dict.get("title", "Untitled"),
        "speaker": field_value_dict.get("speaker", "Unknown"),
        "date": field_value_dict.get("date", "N/A"),
        "context": field_value_dict.get("context", "No context provided"),
        "transcript": field_value_dict.get("transcript", ""),
        "word_count": word_count,
        "top_words": top_words,
        "audio_file": file_path,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = collection.insert_one(new_entry)
        return result.acknowledged
    except PyMongoError:
        return False


def trigger_ml(filepath):
    """
    Triggers machine learning client by sending a signal to ml client by Flask

    Args:
        filepath (str): The file path of the audio file.

    Returns:
        str: the transcript of the audio file if transcript was generated successfully,
        empty string otherwise.
    """
    try:
        # Send the data to ML Client
        print(f"Sending request to ML client at {ML_CLIENT_URL} with file: {filepath}")
        response = requests.post(
            ML_CLIENT_URL, json={"audio_file_path": filepath}, timeout=10
        )

        response_data = response.json()
        print(f"ML client response: {response_data}")
        return response_data
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return "Request exception"
    except ConnectionError:
        return "Connection error"
    except TimeoutError:
        return "Timeout error"


def delete_entry(file_path):
    """
    Deletes an entry from the MongoDB collection by file path.
    Returns True if successful, False if no entry was found or failed.
    """
    if not file_path:
        return False

    try:
        result = collection.delete_one({"_id": file_path})
        return result.deleted_count > 0
    except PyMongoError:
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
    except PyMongoError:
        return False


def update_entry(file_path, update_fields):
    """
    Updates an existing entry in the MongoDB collection.
    Returns True if update was successful, False if failed.
    """
    try:
        result = collection.update_one({"_id": file_path}, {"$set": update_fields})
        return result.modified_count > 0
    except PyMongoError:
        return False


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
