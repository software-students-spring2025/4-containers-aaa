from datetime import datetime, timezone
from app import upload_entry, search_entry
import os
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

if __name__ == "__main__":
    print("\n=== Test: Upload Entry ===")
    file_path = "uploads/test_audio.mp34"
    field_value_dict = {
        "title": "Test Title",
        "speaker": "Test Speaker",
        "date": "2024-01-01",
        "context": "Test context",
        "transcript": "This is a test transcript",
        "word_count": 50,
        "top_words": ["test", "audio", "transcript"],
        "audio_file": file_path,
        "created_at": datetime.now(timezone.utc),
    }
    upload_result = upload_entry(file_path, field_value_dict)
    print("Upload Result:", upload_result)

    print("\n=== Test: Search Entry ===")
    search_result = search_entry(file_path=file_path)
    print("Search Result:", search_result)
