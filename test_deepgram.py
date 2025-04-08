"""
Test script for Deepgram SDK
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

# Try to access the transcription method
if hasattr(deepgram, "transcription"):
    print("transcription method exists")
else:
    print("transcription method does not exist")

# Try to access the listen method
if hasattr(deepgram, "listen"):
    print("listen method exists")
else:
    print("listen method does not exist") 