import datetime
from datetime import datetime

import os
import pyttsx3
import json
from flask import Flask, request, render_template, send_file, jsonify, abort, send_from_directory, redirect, url_for, \
    session
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
from lessons import get_lesson

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


uploaded_modules = []

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])



# Function to extract text from files
def extract_text_from_file(file_path, file_type):
    text = ""
    try:
        if file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif file_type == 'pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file_type == 'docx':
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

# Function to convert text to speech using pyttsx3 and save it to an audio file
def speak_text_to_file(text, audio_file, voice_id=None):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    # If no voice_id is provided, use the first available voice
    if voice_id:
        found_voice = next((voice for voice in voices if voice.id == voice_id), None)
        if found_voice:
            engine.setProperty('voice', voice_id)
        else:
            print(f"Voice ID {voice_id} not found. Using default voice.")
            engine.setProperty('voice', voices[0].id)  # Fallback to the first voice

    engine.save_to_file(text, audio_file)
    engine.runAndWait()

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/LandingPage')
def landingpage():
    return render_template('index2.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

# Route for convert (Text-to-Speech)
@app.route('/convert')
def convert():
    return render_template('convert.html')


@app.route("/docu-viewer/<filename>")
def docu_viewer(filename):
    # File path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    # Debugging: Print file path and type
    print(f"Processing file: {file_path}")

    # Extract text
    file_ext = filename.rsplit('.', 1)[-1].lower()
    content = extract_text_from_file(file_path, file_ext)

    if not content:
        print("No text extracted.")  # Debugging log

    paragraphs = content.split("\n\n")  # Split into paragraphs if needed
    return render_template("docuViewer.html", title=filename, content=paragraphs)


@app.route('/lesson/<chapter>')
def lesson(chapter):
    lesson_data = get_lesson(chapter)  # Use the function to fetch lesson content
    if lesson_data:
        return render_template('lesson.html', title=lesson_data['title'], content=lesson_data['content'])
    return "Chapter not found", 404

# Get available voices (for selection on frontend)
@app.route('/get_voices', methods=['GET'])
def get_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voices_list = [{'id': voice.id, 'name': voice.name} for voice in voices]
    return jsonify(voices_list)

# Route for file upload and TTS conversion
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'voice_id' not in request.form:
        return jsonify({"error": "File or voice selection not provided"}), 400

    file = request.files['file']
    voice_id = request.form['voice_id']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # File extension check
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in ['txt', 'pdf', 'docx']:
        return jsonify({"error": "Unsupported file type"}), 400

    # Sanitize filename to prevent directory traversal or overwriting
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    file.save(file_path)

    # Extract text from the uploaded file
    text = extract_text_from_file(file_path, file_ext)

    if not text:
        return jsonify({"error": "Failed to extract text from the file"}), 500

    # Convert text to speech and save as an audio file
    audio_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.mp3')
    speak_text_to_file(text, audio_file, voice_id)

    # Return both the text and audio file URL
    return jsonify({"text": text, "audio_url": '/download_audio'}), 200



@app.route('/download_audio', methods=['GET'])
def download_audio():
    audio_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.mp3')
    if os.path.exists(audio_file):
        return send_file(audio_file, as_attachment=True, mimetype='audio/mpeg')
    return abort(404)

@app.route('/read_text_aloud', methods=['POST'])
def read_text_aloud():
    data = request.json
    text = data.get('text')
    voice_id = data.get('voice_id')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    audio_file = os.path.join(app.config['UPLOAD_FOLDER'], 'text_output.mp3')
    speak_text_to_file(text, audio_file, voice_id)

    return send_file(audio_file, as_attachment=True, mimetype='audio/mpeg')

# Route for converting paragraph text to speech and playing it (with voice selection)
@app.route('/read_paragraph', methods=['POST'])
def read_paragraph():
    data = request.json
    text = data.get('text')
    voice_id = data.get('voice_id')

    if not text:
        return "No text provided", 400

    audio_file = os.path.join(app.config['UPLOAD_FOLDER'], 'paragraph_output.mp3')
    speak_text_to_file(text, audio_file, voice_id)

    return send_file(audio_file, as_attachment=True, mimetype='audio/mpeg')


METADATA_FILE = "metadata.json"




@app.route('/upload_module', methods=['POST'])
def upload_module():

    if 'file' not in request.files or 'title' not in request.form or 'user_id' not in request.form:
        return jsonify({"error": "File, title, or user ID not provided"}), 400

    user_id = request.form['user_id']
    if not user_id:
        return jsonify({"error": "Invalid user ID"}), 400
    # Extract form data
    title = request.form['title']
    description = request.form.get('description', '')  # Optional
    user_id = request.form['user_id']  # Logged-in user's ID
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # File extension check
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in ['txt', 'pdf', 'docx']:
        return jsonify({"error": "Unsupported file type"}), 400

    # Save file
    safe_filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    file.save(file_path)

    # Save module information
    module_info = {
        "user_id": user_id,
        "title": title,
        "description": description,
        "file_path": safe_filename,
        "uploaded_at": datetime.utcnow().isoformat()
    }

    # Save metadata
    save_metadata(module_info)

    return redirect(url_for('book_page', user_id=user_id))  # Redirect to the book page, passing user_id

    # return redirect(url_for('book_page'))  # Assumes you have a route named 'book'


def save_metadata(module_info):
    metadata_file = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
    try:
        # Check if the metadata file exists, if not, create an empty one
        if not os.path.exists(metadata_file):
            with open(metadata_file, 'w') as file:
                json.dump([], file, indent=4)  # Initialize with an empty list

        with open(metadata_file, 'r') as file:
            metadata = json.load(file)

        # Append new module information
        metadata.append(module_info)

        # Save updated metadata to the file
        with open(metadata_file, 'w') as file:
            json.dump(metadata, file, indent=4)
    except Exception as e:
        print(f"Error saving metadata: {e}")


def load_metadata():
    metadata_file = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
    try:
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as file:
                data = json.load(file)
                # Ensure each entry in the metadata has the required keys
                return [entry for entry in data if isinstance(entry, dict)]
        return []
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return []


@app.route('/book/<user_id>')
def book_page(user_id):
    try:
        # Load metadata and filter modules for the specific user
        uploaded_modules = [module for module in load_metadata() if module.get('user_id') == user_id]
        return render_template('book.html', modules=uploaded_modules)
    except Exception as e:
        print(f"Error loading book page: {e}")
        return "An error occurred while loading the page.", 500




METADATA_FILE = "metadata.json"

@app.route('/delete_file', methods=['POST'])
def delete_file():
    try:
        filename = request.json.get('filename')
        metadata_file = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')

        # Check if metadata file exists
        if not os.path.exists(metadata_file):
            return jsonify({'error': 'Metadata file not found.'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Remove file from metadata list
        metadata = [file for file in metadata if file.get('file_path') != filename]

        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)

        return redirect(url_for('book_page'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/get_user_id', methods=['GET'])
def get_user_id():
    user_id = session.get('user_id')  # Get the user ID from the session
    if user_id:
        return jsonify({"user_id": user_id}), 200
    else:
        return jsonify({"error": "User not logged in"}), 400

if __name__ == '__main__':
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
