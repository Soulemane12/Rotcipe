# backend/app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from dotenv import load_dotenv
from recipe import generate_funny_recipe  # Import the function from your existing recipe.py
from werkzeug.utils import secure_filename
from vision import process_images
from process import process_ingredient_json
import io
import sys
from contextlib import contextmanager

# Load environment variables
load_dotenv(os.path.join('key', '.env'))

app = Flask(__name__, static_folder='../static')  # Update the static folder path

# Add these configurations after creating the Flask app
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class LogCapture:
    def __init__(self):
        self.logs = []
        self._stdout = sys.stdout
        self._stringio = io.StringIO()

    def write(self, string):
        self._stdout.write(string)
        self.logs.append(string.strip())
        
    def flush(self):
        self._stdout.flush()

    def get_logs(self):
        return [log for log in self.logs if log]  # Filter out empty strings

@contextmanager
def capture_logs():
    log_capture = LogCapture()
    sys.stdout = log_capture
    try:
        yield log_capture
    finally:
        sys.stdout = log_capture._stdout

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Check if any files were uploaded
        if 'image0' not in request.files:
            return jsonify({'error': 'No images uploaded'}), 400

        # Process the uploaded images
        images = []
        i = 0
        while f'image{i}' in request.files:
            file = request.files[f'image{i}']
            if file.filename:
                images.append(file)
            i += 1

        # Your existing image processing code here
        # Replace the ingredients.split(',') logic with your image processing

        return jsonify({
            'recipe': 'Your generated recipe here',
            'log': 'Processing completed successfully'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'log': 'An error occurred during processing'
        }), 500

@app.route('/upload', methods=['POST'])
def upload_files():
    with capture_logs() as logs:
        if 'files[]' not in request.files:
            return jsonify({"error": "No files provided", "logs": logs.get_logs()}), 400
        
        files = request.files.getlist('files[]')
        if not files or all(file.filename == '' for file in files):
            return jsonify({"error": "No selected files", "logs": logs.get_logs()}), 400

        print("Starting image processing...")
        uploaded_paths = []
        
        # Process all uploaded files
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_paths.append(filepath)
                print(f"Saved file: {filename}")

        if not uploaded_paths:
            return jsonify({"error": "No valid files uploaded", "logs": logs.get_logs()}), 400

        print(f"Processing {len(uploaded_paths)} images...")
        # Process all images using vision.py
        json_files = process_images(uploaded_paths)
        
        print("Processing identified ingredients...")
        # Process the JSON files using process.py
        ingredients = process_ingredient_json(json_files)
        
        print("Creating recipe...")
        # Generate the recipe
        recipe = generate_funny_recipe(ingredients)

        # Clean up uploaded files
        for filepath in uploaded_paths:
            try:
                os.remove(filepath)
                print(f"Cleaned up file: {filepath}")
            except Exception as e:
                print(f"Error removing file {filepath}: {e}")

        return jsonify({
            "ingredients": ingredients,
            "recipe": recipe,
            "logs": logs.get_logs()
        })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)