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


# Load environment variables from .env file
load_dotenv()


def get_transcript(audio_file: str):
    """
    Async function to transcribe an audio file using the Deepgram API.

    Args:
        audio_file (str): The path to the audio file to transcribe.

    Returns:
        str: The transcript of the audio file.
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
        return f"File operation error: {e}"
    except KeyError as e:
        return f"API response format error: {e}"
    except RuntimeError as e:
        return f"runtime error: {e}"
    except IndexError as e:
        return f"index error: {e}"
    
# def main():
#     audio_file = "testing_audio/Trump_Short_Speech.mp3"
#     transcript = _get_transcript(audio_file)
#     print(transcript)

# if __name__ == "__main__":
#     main()

