from flask import Blueprint, request, jsonify  
from werkzeug.utils import secure_filename  
from groq import Groq    
import os

audio_blueprint = Blueprint('audio_conversion', __name__)

UPLOAD_FOLDER = './audio_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

@audio_blueprint.route('/convert', methods=['POST'])
def convert_audio_to_text():
    """
    Converts uploaded audio file to text using Groq API.
    """
    data = request.get_json()
    file_path = data.get("file")

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found."}), 400

    try:
        # Use the Groq client for transcription
        client = Groq()
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        return jsonify({"transcription": transcription.get("text", "")}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
