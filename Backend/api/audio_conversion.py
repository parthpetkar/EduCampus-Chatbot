from api.common import AudioService
from flask import Blueprint, request, jsonify  
from werkzeug.utils import secure_filename  
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

    try:
        transcription = AudioService.convert_audio_to_text(file_path)
        return jsonify({"transcription": transcription}), 200
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
