"""
Test script to verify that the Deepgram SDK is working correctly.
"""

import os
from dotenv import load_dotenv
from deepgram import Deepgram

# Load environment variables
load_dotenv()

# Initialize the Deepgram SDK
deepgram = Deepgram(os.getenv("DEEPGRAM_API_KEY"))

# Print the available methods
print("Available methods:", dir(deepgram))

# Check if the transcription module exists
if hasattr(deepgram, "transcription"):
    print("transcription module exists")
    print("Transcription module methods:", dir(deepgram.transcription))
else:
    print("transcription module does not exist")

# Check if the prerecorded method exists
if hasattr(deepgram, "transcription") and hasattr(deepgram.transcription, "prerecorded"):
    print("prerecorded method exists")
else:
    print("prerecorded method does not exist")

print("Deepgram SDK version:", deepgram.__version__ if hasattr(deepgram, "__version__") else "Unknown") 