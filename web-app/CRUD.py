import os
from datetime import datetime, timezone
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
        "created_at": datetime.now(timezone.utc)
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
