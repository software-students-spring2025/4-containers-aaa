"""
Detailed test script for Deepgram SDK
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

# Check the transcription module
if hasattr(deepgram, "transcription"):
    print("\nTranscription module methods:", dir(deepgram.transcription))
    
    # Check if sync_prerecorded method exists
    if hasattr(deepgram.transcription, "sync_prerecorded"):
        print("sync_prerecorded method exists")
    else:
        print("sync_prerecorded method does not exist")
        
    # Check if prerecorded method exists
    if hasattr(deepgram.transcription, "prerecorded"):
        print("prerecorded method exists")
    else:
        print("prerecorded method does not exist")
else:
    print("transcription module does not exist") 