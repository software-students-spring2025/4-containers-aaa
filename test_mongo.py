import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    # Get MongoDB connection details from environment variables
    mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "voice_data")

    # Connect to MongoDB
    client = MongoClient(f"mongodb://{mongo_username}:{mongo_password}@localhost:{mongo_port}/")
    db = client[mongo_db_name]
    print("Connected to MongoDB")

    # Test data insertion
    result = db.transcriptions.insert_one({"title": "Python Test", "speaker": "Bob", "transcript": "Test from Python"})
    print("Inserted document ID:", result.inserted_id)

    # Retrieve and print documents
    for doc in db.transcriptions.find():
        print(doc)
except Exception as e:
    print("Error connecting to MongoDB:", e)
