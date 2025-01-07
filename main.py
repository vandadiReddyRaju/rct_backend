# main.py

import os
import glob
from ide_qr_bot_v0 import QRBot
from copy_folder_to_docker import prepare_docker_environment
from helpers import get_question_details_from_zip  # Removed get_question_details import

# Inputs
user_query = """<p>
Can you help me with my mistakes.
</p>"""

def get_latest_zip(downloads_folder=None):
    if downloads_folder is None:
        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    
    list_of_zips = glob.glob(os.path.join(downloads_folder, "*.zip"))
    if not list_of_zips:
        raise FileNotFoundError("No zip files found in the Downloads folder.")
        
    latest_zip = max(list_of_zips, key=os.path.getctime)
    filename = os.path.splitext(os.path.basename(latest_zip))[0]
    filename = filename.replace(" (zip)", "").strip()
    
    print(f"Processing zip file: {filename}")
    return latest_zip, filename

def main():
    try:
        latest_zip_path, zip_filename = get_latest_zip()
        print(f"Processing file: {zip_filename}")
        
        # Retrieve question details from the CSV
        question_details = get_question_details_from_zip(zip_filename)
        if not question_details:
            print(f"No question details found for: {zip_filename}")
            return
        
        question_command_id = question_details['question_command_id']
        question_content = question_details['question_content']
        question_test_cases = question_details['question_test_cases']
        
        print(f"Mapped Question Command ID: {question_command_id}")
        print(f"Question Content: {question_content}")
        print(f"Question Test Cases: {question_test_cases}")
        
        container_id = "09769941a48c"  # **Update with your container ID or manage dynamically**
        
        # Use question_command_id as output_folder
        output_folder = question_command_id
        
        # Step 1: Prepare Docker environment
        prepare_docker_environment(question_command_id, latest_zip_path, container_id)
        
        # Step 2: Initialize QRBot and get response
        qrbot = QRBot(
            user_query=user_query,
            question_id=question_command_id,  # Assuming QRBot expects 'question_id' to be 'question_command_id'
            zip_path=latest_zip_path,
            question_content=question_content,
            question_test_cases=question_test_cases
        )
        output = qrbot.get_bot_response()
        print(f"Bot Response: {output}")  # Or handle the output as needed
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
