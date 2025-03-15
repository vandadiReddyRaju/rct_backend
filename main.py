from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import os
import glob
from werkzeug.utils import secure_filename
from ide_qr_bot_v0 import QRBot
from helpers import get_question_details_from_zip
import traceback
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    logging.info("Root route accessed")
    return "Welcome to the RCT Backend!"

@app.route('/api/process', methods=['POST'])
def process_request():
    # Check if the request contains a file and a query
    if 'file' not in request.files or 'query' not in request.form:
        return jsonify({'error': 'Missing file or query in request'}), 400

    file = request.files['file']
    user_query = request.form['query']

    # Validate the file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Only ZIP files are accepted.'}), 400

    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Retrieve question details from the ZIP file
        zip_filename = os.path.splitext(filename)[0]
        question_details = get_question_details_from_zip(zip_filename)
        if not question_details:
            return jsonify({'response': f'No question details found for: {zip_filename}'})

        question_command_id = question_details['question_command_id']
        question_content = question_details['question_content']
        question_test_cases = question_details['question_test_cases']

        # Initialize QRBot and get response
        qrbot = QRBot(
            user_query=user_query,
            question_id=question_command_id,
            zip_path=file_path,
            question_content=question_content,
            question_test_cases=question_test_cases
        )
        output = qrbot.get_bot_response()
        logging.info(f"Backend Output: {output}")  # Debugging: Print the output

        # Ensure the output is a valid JSON-serializable object
        if not isinstance(output, (dict, list, str, int, float, bool)):
            output = str(output)  # Convert to string if not JSON-serializable

        # Return the bot response as JSON
        return jsonify({'response': output})

    except Exception as e:
        # Log the full traceback for debugging
        print(f"Error in process_request: {str(e)}")
        traceback.print_exc()  # Print the full traceback
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
