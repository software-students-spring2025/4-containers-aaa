"""
Flask application for ml client to receive signals from frontend
"""

import os
from flask import Flask, request, jsonify
from ml_client import get_transcript


app = Flask(__name__)


@app.route("/get-transcripts", methods=["POST"])
def process_image_api():
    """
    API to get transcript from deepgram
    """
    data = request.get_json()
    voice_data_rel_file_path = data.get("audio_file_path")

    print(voice_data_rel_file_path)

    if not voice_data_rel_file_path:
        return jsonify({"message": "No audio file path provided"}), 400

    file_path = os.path.join("..", voice_data_rel_file_path)
    result = get_transcript(file_path)
    print(result)
    return jsonify({"transcript": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
