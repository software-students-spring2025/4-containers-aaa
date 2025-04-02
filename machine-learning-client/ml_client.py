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

load_dotenv()


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
        print(transcript)

    except (OSError, IOError) as e:
        print(f"File operation error: {e}")
    except KeyError as e:
        print(f"API response format error: {e}")
    except RuntimeError as e:
        print(f"runtime error: {e}")
    except IndexError as e:
        print(f"index error: {e}")


def main():
    """
    This function is the main entry point for the program.
    """
    selected_audio_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testing_audio",
        "Trump_Short_Speech.mp3",
    )
    get_transcript(selected_audio_file)


if __name__ == "__main__":
    main()
