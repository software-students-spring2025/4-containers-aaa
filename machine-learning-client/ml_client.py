"""
This program is used to transcribe audio files using the Deepgram API.
"""

import os
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)
from pymongo import MongoClient, errors


# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
mongo_port = os.getenv("MONGO_PORT", "27017")
mongo_db_name = os.getenv("MONGO_DB_NAME", "voice_data")

client = MongoClient(
    f"mongodb://{mongo_username}:{mongo_password}@localhost:{mongo_port}/"
)

# client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
db = client[mongo_db_name]
collection = db["transcriptions"]

# Start the replica set mode
try:
    client.admin.command("replSetInitiate")
    print("Replica set initiated.")
except Exception as e:
    print("Error:", e)


def get_transcript(audio_file: str):
    """
    This function transcribes an audio file using the Deepgram API.
    """
    try:
        deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
        )

        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
        transcript = response.results.channels[0].alternatives[0].transcript
        return transcript

    except (OSError, IOError) as e:
        print(f"File operation error: {e}")
    except KeyError as e:
        print(f"API response format error: {e}")
    except RuntimeError as e:
        print(f"runtime error: {e}")
    except IndexError as e:
        print(f"index error: {e}")
