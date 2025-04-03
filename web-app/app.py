"""
The main file for the web application.
This file contains the routes for the web application.
"""



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




#CRUD 
def upload_entry(file_path, title=None, speaker=None, date=None, context=None, word_count=0, top_words=None):
    """
    Uploads an entry to the MongoDB collection with the given metadata.
    Stores default values if fields are empty or None.
    """
    new_entry = {
        "_id": file_path,
        "title": title if title else "Untitled",
        "speaker": speaker if speaker else "Unknown",
        "date": date if date else "N/A",
        "context": context if context else "No context provided",
        "transcript": "",
        "word_count": word_count,
        "top_words": top_words if top_words else [],
        "audio_file": file_path,
        "created_at": datetime.utcnow()
    }

    try:
        result = collection.insert_one(new_entry)
        return result.acknowledged
    except Exception:
        return False

def delete_entry(file_path):
    """
    Deletes an entry from the MongoDB collection by file path.
    Returns True if successful, False if no entry was found or failed.
    """
    try:
        result = collection.delete_one({"_id": file_path})
        return result.deleted_count > 0  
    except Exception:
        return False


def search_entry(file_path=None, title=None, speaker=None):
    """
    Searches for entries in the MongoDB collection based on file path, title, or speaker.
    Performs a partial and case-insensitive match.
    Returns list of matching documents if found，False if no matching entries are found.
    """
    query = {}

    if file_path:
        query["_id"] = {"$regex": file_path, "$options": "i"}

    if title:
        query["title"] = {"$regex": title, "$options": "i"}

    if speaker:
        query["speaker"] = {"$regex": speaker, "$options": "i"}

    results = list(collection.find(query))
    return results if results else False


#update_entry("uploads/audio_001.mp3", {"speaker": "John", "context": "Updated meeting notes"})
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
    except Exception:
        return False



if __name__ == "__main__":
    app.run(debug=True)
    search_entry()


