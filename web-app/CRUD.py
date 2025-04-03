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


file_path = "uploads/audio_test.mp3"
title = "Test Audio"
speaker = "Test Speaker"
date = "2025-04-01"
context = "Testing audio upload"
word_count = 120
top_words = ["test", "audio", "upload"]

# Test upload_entry
print("\n=== Test: Upload Entry ===")
upload_success = upload_entry(file_path, title, speaker, date, context, word_count, top_words)
if upload_success:
    print("Upload successful.")
else:
    print("Upload failed.")

# Verify upload
uploaded_entry = collection.find_one({"_id": file_path})
if uploaded_entry:
    print("Entry found in database after upload.")
else:
    print("Entry not found in database after upload.")

# Test search_entry
print("\n=== Test: Search Entry ===")
search_results = search_entry(file_path="audio_test")
if search_results:
    print("Search successful. Found entries:")
    for entry in search_results:
        print(entry)
else:
    print("Search failed or no entries found.")

# Test update_entry
print("\n=== Test: Update Entry ===")
update_fields = {"speaker": "Updated Speaker", "context": "Updated context"}
update_success = update_entry(file_path, update_fields)
if update_success:
    print("Update successful.")
else:
    print("Update failed.")

# Verify update
updated_entry = collection.find_one({"_id": file_path})
if updated_entry:
    print("Updated Entry in Database:")
    print("Speaker:", updated_entry.get("speaker"))
    print("Context:", updated_entry.get("context"))
else:
    print("Updated entry not found in database.")

# Test delete_entry
print("\n=== Test: Delete Entry ===")
delete_success = delete_entry(file_path)
if delete_success:
    print("Delete successful.")
else:
    print("Delete failed or entry not found.")

# Verify deletion
deleted_entry = collection.find_one({"_id": file_path})
if deleted_entry:
    print("Entry still exists in database after deletion (unexpected).")
else:
    print("Entry successfully deleted from database.")