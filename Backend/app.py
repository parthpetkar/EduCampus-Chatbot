from flask import Flask, jsonify, request  
from api.retrieval import retrieval_blueprint
from api.generation import generation_blueprint
from api.chat_with_pdf import chat_blueprint
from api.audio_conversion import audio_blueprint
from config import config
from flask_cors import CORS  
from werkzeug.utils import secure_filename  
import os

app = Flask(__name__)
app.config.from_object(config)
CORS(app, supports_credentials=False)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Register the blueprints for modular routes
app.register_blueprint(retrieval_blueprint, url_prefix="/api/retrieval")
app.register_blueprint(generation_blueprint, url_prefix="/api/generation")
app.register_blueprint(chat_blueprint, url_prefix="/api/chat_with_pdf")
app.register_blueprint(audio_blueprint, url_prefix="/api/audio_conversion")

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/query', methods=['POST'])
def query():
    """
    Route to handle user choice between retrieval, generation, and chat with PDF modes.
    """
    query = request.form.get("query", "")
    uploaded_file = request.files.get("file")

    if not query:
        return jsonify({"error": "No query provided."}), 400

    if uploaded_file:
        # Save the uploaded file
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")
        uploaded_file.save(file_path)

        # Call the chat_with_pdf endpoint
        response = app.test_client().post(
            '/api/chat_with_pdf/generate',
            json={"file": file_path, "query": query}
        ).get_data(as_text=True)
        return jsonify({"response": response}), 200

    # Call the text generation endpoint if no file is uploaded
    response = app.test_client().post(
        '/api/generation/generate',
        json={"query": query}
    ).get_data(as_text=True)
    return jsonify({"response": response}), 200


@app.route('/api/upload_audio', methods=['POST'])
def audio():
    """
    Route to handle audio file uploads and invoke the audio conversion endpoint.
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    audio_file = request.files['audio']
    if not audio_file.filename:
        return jsonify({"error": "Empty file uploaded."}), 400

    # Save the audio file securely
    filename = secure_filename(audio_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")
    audio_file.save(file_path)

    # Call the audio conversion endpoint
    response = app.test_client().post(
        '/api/audio_conversion/convert',
        json={"file": file_path}
    ).get_data(as_text=True)
    return jsonify({"response": response}), 200


if __name__ == "__main__":
    app.run(debug=config.DEBUG)

# python -m venv myenv   
# ./myenv 
#./myenv/Scripts/activate