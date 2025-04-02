"""
The main file for the web application.
This file contains the routes for the web application.
"""

import os
from datetime import datetime
from mutagen.easyid3 import EasyID3
from flask import Flask, render_template, request

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

            audio = EasyID3(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            audio["title"] = title
            audio["artist"] = speaker
            audio["date"] = date
            audio.save()
        except (OSError, IOError) as e:
            print("Error saving metadata:", e)
            return "Error saving metadata", 500

    return "File uploaded successfully", 200


if __name__ == "__main__":
    app.run(debug=True)
