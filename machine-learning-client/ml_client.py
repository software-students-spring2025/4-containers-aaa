"""
This program is used to transcribe audio files using the Deepgram API.
"""

import os
from dotenv import load_dotenv
from deepgram import Deepgram


def get_transcript(audio_file: str):
    """
    This function transcribes an audio file using the Deepgram API.
    """
    try:
        # Initialize the Deepgram SDK
        deepgram = Deepgram(os.getenv("DEEPGRAM_API_KEY"))

        # Open the audio file
        with open(audio_file, "rb") as file:
            source = {"buffer": file, "mimetype": "audio/wav"}

        # Set the transcription options
        options = {
            "smart_format": True,
            "model": "nova-3",
        }

        # Send the request to Deepgram
        response = deepgram.transcription.prerecorded(source, options)
        
        # Extract the transcript from the response
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        return transcript

    except (OSError, IOError) as e:
        return f"File operation error: {e}"
    except KeyError as e:
        return f"API response format error: {e}"
    except Exception as e:
        return f"Error: {e}"
