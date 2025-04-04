"""
The main file for the web application.
This file contains the routes for the web application.
"""

import os
import re
from collections import Counter
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import requests


# Load environment variables from .env file
load_dotenv()


# Connect to MongoDB
mongo_host = os.getenv("MONGO_HOST", "localhost")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
mongo_db_name = os.getenv("MONGO_DB_NAME", "voice_data")

client = MongoClient(
    f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/"
)
db = client[mongo_db_name]
collection = db["transcriptions"]

# ML Settings
ML_CLIENT_URL = os.getenv("ML_CLIENT_URL", "http://127.0.0.1:6000/get-transcripts")

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

            # Save metadata using upload_entry function
            if not upload_entry(filepath, metadata):
                print("Error uploading entry to MongoDB")
                return "Error saving metadata to database", 500

        except (OSError, IOError) as e:
            print("Error during data processing:", e)
            return "Error during data processing", 500

    return "File uploaded successfully", 200


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

    # Try to send to ML for transcript
    transcript = ""
    # try:
    #     transcript = trigger_ml(file_path)
    # except requests.exceptions.RequestException as e:
    #     print("Error from ML",e)

    word_count = 0
    if len(transcript) != 0:
        word_count = len(transcript)

    # Create a new entry with default values or values from the dictionary
    new_entry = {
        "_id": file_path,
        "title": field_value_dict.get("title", "Untitled"),
        "speaker": field_value_dict.get("speaker", "Unknown"),
        "date": field_value_dict.get("date", "N/A"),
        "context": field_value_dict.get("context", "No context provided"),
        "transcript": transcript,
        "word_count": word_count,
        "top_words": field_value_dict.get("top_words", []),
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
        response = requests.post(
            ML_CLIENT_URL, json={"audio_file_path": filepath}, timeout=10
        )

        if response.status_code != 200:
            return redirect(url_for("index"))

        response_data = response.json()
        if response_data.get("transcript"):
            return response_data.get("transcript")
        return ""
    except requests.exceptions.RequestException:
        return ""


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


def get_transcript(file_path):
    """
    get transcript from mongoDB by _id
    """
    entry = collection.find_one({"_id": file_path})
    transcript = entry["transcript"]
    if entry and "transcript" in entry:
        return transcript
    return ""


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


def rank_by_freq_desc(pairs):
    """
    rank words by frequency descending
    """
    return sorted(pairs, key=lambda x: x[1], reverse=True)


def get_entry(file_path):
    """
    get entry from mongoDB
    """
    entry = collection.find_one({"_id": file_path})
    return entry


def trans_to_top_word(file_path):
    """
    1. get_transcript(file_path)
    2. parse_transcript(transcript)
    3. rank_by_freq_desc(pairs)
    4. update_entry()
    """
    transcript = get_transcript(file_path)
    parsed = parse_transcript(transcript)
    ranked = rank_by_freq_desc(parsed)
    update_entry(file_path, {"top_words": ranked})


if __name__ == "__main__":
    app.run(debug=True)
